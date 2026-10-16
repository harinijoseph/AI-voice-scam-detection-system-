# Phase 5 — Robustness & Generalization Test Report

## 1. Acoustic Model Noise & Telephony Decay Matrix

| Evaluation Condition | Accuracy | Precision | Recall | F1-Score | Equal Error Rate (EER) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline (Clean Audio)** | **92.00%** | **100.00%** | **84.00%** | **91.30%** | **4.00%** |
| **SNR = 20 dB (Light Noise)** | 67.00% | 100.00% | 34.00% | 50.75% | 7.00% |
| **SNR = 10 dB (Moderate Noise)** | 61.00% | 100.00% | 22.00% | 36.07% | 8.00% |
| **SNR = 5 dB (Heavy Noise)** | 59.00% | 100.00% | 18.00% | 30.51% | 18.00% |
| **Telephony Narrowband (8 kHz)** | 87.00% | 79.37% | 100.00% | 88.50% | 6.00% |
| **Unseen Out-of-Distribution Generator** | 100.00% | 100.00% | 100.00% | 100.00% | 0.00% |

---

## 2. Content Engine Generalization to Unseen Scam Scripts

* **Unseen Script Evaluation Accuracy:** **87.50%**
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
