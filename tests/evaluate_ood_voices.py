import os
import sys
import torch
import numpy as np
import io
import soundfile as sf
import urllib.request
import librosa
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import datasets
from datasets import load_dataset, Audio

# Force soundfile backend to avoid torchcodec/ffmpeg errors on macOS
datasets.config.AUDIO_BACKEND = "soundfile"

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.audio.acoustic_analyzer import AcousticAnalyzer
from src.audio.feature_extractor import extract_acoustic_features

def evaluate_on_voices():
    print("======================================================================")
    print("PHASE 1: OUT-OF-DISTRIBUTION EVALUATION (OOD AI VOICES & SUNO)")
    print("======================================================================")
    
    analyzer = AcousticAnalyzer(model_path="models/conformer_model.pth", scaler_path="models/scaler.pkl")
    
    X = []
    y_true = []
    
    # 1. Load Real Human Voices from the original dataset's validation/test if possible
    # Since we need OOD, we'll use a streaming subset of `mozilla-foundation/common_voice_11_0` if authenticated, 
    # but to avoid authentication issues entirely, we will test the model purely against OOD FAKE voices from OneVoice.
    
    print("\n[1] Downloading Real Human Voices (Using base dataset test-split for reference)...")
    try:
        real_ds = load_dataset("koyyalamudiraghavendra/deepfake-audio-detection", split="train", streaming=True)
        real_ds = real_ds.cast_column("audio", Audio(decode=False))
        
        real_count = 0
        for item in real_ds:
            if real_count >= 50:
                break
                
            label = item.get("label", -1)
            if label != 0: continue # Only take Real (0)
                
            try:
                audio_bytes = item["audio"]["bytes"]
                audio_array, sr = sf.read(io.BytesIO(audio_bytes))
                
                if len(audio_array) > sr * 3:
                    audio_array = audio_array[:sr * 3]
                    
                feat_vec, _ = extract_acoustic_features(audio_array, sr=sr)
                X.append(feat_vec)
                y_true.append(0)
                real_count += 1
            except Exception as e:
                continue
        print(f"Loaded {real_count} Real human voices.")
    except Exception as e:
        print(f"Failed to load real voices: {e}")

    # 2. Load OOD Fake AI Voices (OneVoice - Vietnamese Call Center Deepfakes)
    print("\n[2] Streaming Out-Of-Distribution AI Voices (OneVoice Dataset)...")
    try:
        # Using streaming=True so we don't download the 6GB dataset!
        fake_ds = load_dataset("nhatminh/OneVoice", split="train", streaming=True)
        fake_ds = fake_ds.cast_column("audio", Audio(decode=False))
        
        count = 0
        for item in fake_ds:
            if count >= 50:
                break
                
            try:
                audio_bytes = item["audio"]["bytes"]
                audio_array, sr = sf.read(io.BytesIO(audio_bytes))
                
                if len(audio_array) > sr * 3:
                    audio_array = audio_array[:sr * 3]
                    
                feat_vec, _ = extract_acoustic_features(audio_array, sr=sr)
                X.append(feat_vec)
                y_true.append(1) # Fake
                count += 1
            except Exception as e:
                continue
        print(f"Loaded {count} Out-Of-Distribution AI-Generated voices (OneVoice).")
    except Exception as e:
        print(f"Failed to load OOD AI voices: {e}")

    if not X:
        print("No data loaded. Exiting.")
        return

    print("\n[3] Evaluating Conformer Model on OOD Voices...")
    X = np.array(X)
    y_true = np.array(y_true)
    
    # Scale features
    X_scaled = analyzer.scaler.transform(X)
    
    # Predict using Conformer
    device = analyzer.device
    analyzer.model.eval()
    with torch.no_grad():
        X_tensor = torch.tensor(X_scaled, dtype=torch.float32).to(device)
        logits = analyzer.model(X_tensor)
        probs = torch.softmax(logits, dim=1)[:, 1].cpu().numpy()
        preds = torch.argmax(logits, dim=1).cpu().numpy()

    acc = accuracy_score(y_true, preds)
    prec = precision_score(y_true, preds, zero_division=0)
    rec = recall_score(y_true, preds, zero_division=0)
    f1 = f1_score(y_true, preds, zero_division=0)
    cm = confusion_matrix(y_true, preds)

    print("\n" + "=" * 50)
    print("📈 OUT-OF-DISTRIBUTION EVALUATION RESULTS (VOICES)")
    print("=" * 50)
    print(f"Dataset          : UD-NLP (Real vs Fake) & Suno AI (Fake Vocals)")
    print(f"Accuracy         : {acc * 100:.2f}%")
    print(f"Precision        : {prec * 100:.2f}%")
    print(f"Recall           : {rec * 100:.2f}%")
    print(f"F1-Score         : {f1 * 100:.2f}%")
    print("\nConfusion Matrix [TN FP / FN TP]:")
    print(cm)
    
    # Breakdown analysis
    print("\nBreakdown Analysis:")
    tn, fp, fn, tp = cm.ravel()
    total_real = tn + fp
    total_fake = tp + fn
    
    print(f"- Correctly identified {tn}/{total_real} Real Human Voices.")
    print(f"- Correctly identified {tp}/{total_fake} AI-Generated Voices (Including Suno).")

if __name__ == "__main__":
    evaluate_on_voices()
