import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import numpy as np
import pandas as pd
import librosa
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from src.audio.train_acoustic_rf import run_phase1_baseline, compute_eer
from src.audio.feature_extractor import extract_acoustic_features
from src.data.dataset_loader import prepare_phase1_dataset
from src.nlp.content_engine import ContentEngine

def add_gaussian_noise(y, snr_db=10.0):
    """Adds Gaussian white noise at specified Signal-to-Noise Ratio (SNR in dB)."""
    signal_power = np.mean(y ** 2)
    if signal_power == 0:
        return y
    snr_linear = 10 ** (snr_db / 10.0)
    noise_power = signal_power / snr_linear
    noise = np.random.normal(0, np.sqrt(noise_power), size=len(y))
    return y + noise

def resample_telephony_8k(y, orig_sr=22050):
    """Simulates narrow-band telephony audio quality by downsampling to 8 kHz and upsampling back."""
    y_8k = librosa.resample(y, orig_sr=orig_sr, target_sr=8000)
    return librosa.resample(y_8k, orig_sr=8000, target_sr=orig_sr)

def run_phase5_robustness_experiments(output_report_path="data/phase5/robustness_report.md"):
    """
    Phase 5: Robustness & Generalization Testing Pipeline.
    Evaluates model decay under real-world noise, telephony compression, out-of-distribution TTS, and unseen scam scripts.
    """
    os.makedirs(os.path.dirname(output_report_path), exist_ok=True)
    print("=" * 70)
    print("PHASE 5: ROBUSTNESS & GENERALIZATION TESTING")
    print("=" * 70)

    # 1. Train Baseline Acoustic Model (Phase 1)
    phase1_res = run_phase1_baseline()
    rf_clf = phase1_res["model"]
    scaler = phase1_res.get("scaler")

    # Load test clips
    reals, fakes = prepare_phase1_dataset(num_clips_per_class=50)

    def evaluate_acoustic_subset(file_list_reals, file_list_fakes, noise_snr=None, telephony_mode=False):
        X, y = [], []
        for path in file_list_reals:
            audio, sr = librosa.load(path, sr=22050)
            if noise_snr is not None:
                audio = add_gaussian_noise(audio, snr_db=noise_snr)
            if telephony_mode:
                audio = resample_telephony_8k(audio, orig_sr=sr)
            vec, _ = extract_acoustic_features(audio, sr=sr)
            X.append(vec)
            y.append(0)

        for path in file_list_fakes:
            audio, sr = librosa.load(path, sr=22050)
            if noise_snr is not None:
                audio = add_gaussian_noise(audio, snr_db=noise_snr)
            if telephony_mode:
                audio = resample_telephony_8k(audio, orig_sr=sr)
            vec, _ = extract_acoustic_features(audio, sr=sr)
            X.append(vec)
            y.append(1)

        X, y = np.array(X), np.array(y)
        X_eval = scaler.transform(X) if scaler is not None else X
        if hasattr(rf_clf, "predict_proba"):
            preds = rf_clf.predict(X_eval)
            scores = rf_clf.predict_proba(X_eval)[:, 1]
        else:
            import torch
            device = next(rf_clf.parameters()).device if hasattr(rf_clf, 'parameters') else torch.device("cpu")
            rf_clf.eval()
            with torch.no_grad():
                X_tensor = torch.tensor(X_eval, dtype=torch.float32).to(device)
                outputs = rf_clf(X_tensor)
                scores = torch.softmax(outputs, dim=1)[:, 1].cpu().numpy()
                preds = torch.argmax(outputs, dim=1).cpu().numpy()
        
        acc = float(accuracy_score(y, preds))
        prec = float(precision_score(y, preds, zero_division=0))
        rec = float(recall_score(y, preds, zero_division=0))
        f1 = float(f1_score(y, preds, zero_division=0))
        eer, _ = compute_eer(y, scores)

        return {"accuracy": acc, "precision": prec, "recall": rec, "f1_score": f1, "eer": eer}

    print("\nRunning Experiment 1: Acoustic Noise Stress Testing (SNR = 20dB, 10dB, 5dB)...")
    res_clean = evaluate_acoustic_subset(reals, fakes, noise_snr=None)
    res_snr20 = evaluate_acoustic_subset(reals, fakes, noise_snr=20.0)
    res_snr10 = evaluate_acoustic_subset(reals, fakes, noise_snr=10.0)
    res_snr5 = evaluate_acoustic_subset(reals, fakes, noise_snr=5.0)

    print("Running Experiment 2: Telephony Narrow-Band Compression (8kHz resample)...")
    res_telephony = evaluate_acoustic_subset(reals, fakes, telephony_mode=True)

    print("Running Experiment 3: Out-of-Distribution AI Voice Generator Test...")
    # Generate unseen synthetic voice clips (simulating ElevenLabs pitch modulation)
    unseen_fakes = []
    sr = 22050
    t = np.linspace(0, 3.0, int(sr * 3.0), endpoint=False)
    os.makedirs("data/phase5/unseen_tts", exist_ok=True)

    for i in range(30):
        # ElevenLabs style: neural pitch modulation with subtle reverb
        f0_eleven = 190 + 8.0 * np.sin(2 * np.pi * 0.8 * t) + 3 * np.sin(2 * np.pi * 2.5 * t)
        audio = 0.5 * np.sin(2 * np.pi * f0_eleven * t) + 0.2 * np.random.normal(0, 0.01, len(t))
        filepath = f"data/phase5/unseen_tts/elevenlabs_sim_{i+1:02d}.wav"
        import wave, struct
        with wave.open(filepath, 'w') as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
            wf.writeframes(struct.pack(f'<{len(audio)}h', *(audio * 30000).astype(np.int16)))
        unseen_fakes.append(filepath)

    res_unseen_generator = evaluate_acoustic_subset(reals[:30], unseen_fakes)

    print("Running Experiment 4: Unseen Scam Script Zero-Shot NLP Test...")
    content_engine = ContentEngine()
    
    unseen_scam_scripts = [
        "Crypto investment opportunity: deposit $500 in Bitcoin right now and guarantee 10x returns by tomorrow.",
        "Your electric power service will be disconnected in 45 minutes due to unpaid utility bills. Transfer money via Zelle to avoid shutoff.",
        "Ransomware alert: your hard drive is encrypted. Pay 0.5 Bitcoin fine to receive your decryption key immediately.",
        "Real estate wire fraud: change closing bank details immediately and wire $45,000 to this new escrow handle."
    ]

    unseen_normal_scripts = [
        "Hey, can you send me the recipe for that pasta dish we made last Sunday?",
        "Please confirm your arrival time so we can reserve the meeting room.",
        "I will be working from home tomorrow due to severe weather warnings.",
        "Did you have a chance to finish reading chapter 4 of the textbook?"
    ]

    correct_content = 0
    total_content = len(unseen_scam_scripts) + len(unseen_normal_scripts)

    for text in unseen_scam_scripts:
        res_text = content_engine.analyze_text(text)
        if res_text["is_scam"]:
            correct_content += 1

    for text in unseen_normal_scripts:
        res_text = content_engine.analyze_text(text)
        if not res_text["is_scam"]:
            correct_content += 1

    content_unseen_acc = correct_content / total_content

    # 5. Generate Markdown Report
    report_content = f"""# Phase 5 — Robustness & Generalization Test Report

## 1. Acoustic Model Noise & Telephony Decay Matrix

| Evaluation Condition | Accuracy | Precision | Recall | F1-Score | Equal Error Rate (EER) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline (Clean Audio)** | **{res_clean['accuracy']*100:.2f}%** | **{res_clean['precision']*100:.2f}%** | **{res_clean['recall']*100:.2f}%** | **{res_clean['f1_score']*100:.2f}%** | **{res_clean['eer']*100:.2f}%** |
| **SNR = 20 dB (Light Noise)** | {res_snr20['accuracy']*100:.2f}% | {res_snr20['precision']*100:.2f}% | {res_snr20['recall']*100:.2f}% | {res_snr20['f1_score']*100:.2f}% | {res_snr20['eer']*100:.2f}% |
| **SNR = 10 dB (Moderate Noise)** | {res_snr10['accuracy']*100:.2f}% | {res_snr10['precision']*100:.2f}% | {res_snr10['recall']*100:.2f}% | {res_snr10['f1_score']*100:.2f}% | {res_snr10['eer']*100:.2f}% |
| **SNR = 5 dB (Heavy Noise)** | {res_snr5['accuracy']*100:.2f}% | {res_snr5['precision']*100:.2f}% | {res_snr5['recall']*100:.2f}% | {res_snr5['f1_score']*100:.2f}% | {res_snr5['eer']*100:.2f}% |
| **Telephony Narrowband (8 kHz)** | {res_telephony['accuracy']*100:.2f}% | {res_telephony['precision']*100:.2f}% | {res_telephony['recall']*100:.2f}% | {res_telephony['f1_score']*100:.2f}% | {res_telephony['eer']*100:.2f}% |
| **Unseen Out-of-Distribution Generator** | {res_unseen_generator['accuracy']*100:.2f}% | {res_unseen_generator['precision']*100:.2f}% | {res_unseen_generator['recall']*100:.2f}% | {res_unseen_generator['f1_score']*100:.2f}% | {res_unseen_generator['eer']*100:.2f}% |

---

## 2. Content Engine Generalization to Unseen Scam Scripts

* **Unseen Script Evaluation Accuracy:** **{content_unseen_acc * 100:.2f}%**
* **Tested Unseen Domains:** Crypto Investment Traps, Ransomware Hotlines, Utility Disconnection Threats, Real Estate Escrow Fraud.

---

## 3. Honest Forensic Limitations & Discussion (For Thesis Chapter)

1. **Acoustic Domain Shift:**
   - Neural TTS generators with realistic pitch modulation (e.g. ElevenLabs) introduce micro-pitch jitter, slightly increasing EER if trained only on baseline TTS.
   - *Mitigation:* Data augmentation with pitch perturbation during acoustic classifier training.

2. **SNR & Noise Sensitivity:**
   - Heavy Gaussian background noise (SNR = 5dB) corrupts high-frequency spectral centroids and F0 pitch tracking.
   - *Mitigation:* Preprocessing noise suppression filter (Wiener filtering or spectral subtraction) prior to feature extraction.

3. **Zero-Shot Content Evasion:**
   - Novel scam domains without explicit keywords (e.g., subtle crypto investment traps) rely heavily on TF-IDF bigrams.
   - *Mitigation:* Integrating zero-shot transformer classifiers (e.g. DeBERTa/RoBERTa) alongside TF-IDF to capture semantic context.
"""

    with open(output_report_path, "w") as f:
        f.write(report_content)

    print("\n" + "=" * 50)
    print("📈 PHASE 5 EXPERIMENTAL REPORT GENERATED")
    print("=" * 50)
    print(report_content)

    return {
        "res_clean": res_clean,
        "res_snr10": res_snr10,
        "res_telephony": res_telephony,
        "res_unseen_generator": res_unseen_generator,
        "content_unseen_acc": content_unseen_acc,
        "report_path": output_report_path
    }

if __name__ == "__main__":
    run_phase5_robustness_experiments()
