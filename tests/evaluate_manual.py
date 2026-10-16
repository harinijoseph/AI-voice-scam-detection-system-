import os
import sys
import torch
import numpy as np
import librosa
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import glob

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.audio.acoustic_analyzer import AcousticAnalyzer
from src.audio.feature_extractor import extract_acoustic_features

def evaluate_manual_directory(base_dir="data/manual_test"):
    print("======================================================================")
    print("PHASE 1: MANUAL OUT-OF-DISTRIBUTION EVALUATION")
    print("======================================================================")
    
    analyzer = AcousticAnalyzer(model_path="models/conformer_model.pth", scaler_path="models/scaler.pkl")
    
    real_dir = os.path.join(base_dir, "real")
    fake_dir = os.path.join(base_dir, "fake")
    
    X = []
    y_true = []
    
    # 1. Load Real Files
    real_files = glob.glob(os.path.join(real_dir, "*.*"))
    real_count = 0
    print(f"\n[1] Found {len(real_files)} Real audio files. Extracting features...")
    for file in real_files:
        try:
            # We use librosa because it supports .wav, .mp3, .flac, .ogg, etc. out of the box
            audio_array, sr = librosa.load(file, sr=16000)
            
            # Truncate to 3 seconds for consistency with training
            if len(audio_array) > sr * 3:
                audio_array = audio_array[:sr * 3]
                
            feat_vec, _ = extract_acoustic_features(audio_array, sr=sr)
            X.append(feat_vec)
            y_true.append(0) # Real
            real_count += 1
        except Exception as e:
            print(f"Skipping {os.path.basename(file)}: {e}")

    # 2. Load Fake Files
    fake_files = glob.glob(os.path.join(fake_dir, "*.*"))
    fake_count = 0
    print(f"\n[2] Found {len(fake_files)} Fake AI audio files. Extracting features...")
    for file in fake_files:
        try:
            audio_array, sr = librosa.load(file, sr=16000)
            
            if len(audio_array) > sr * 3:
                audio_array = audio_array[:sr * 3]
                
            feat_vec, _ = extract_acoustic_features(audio_array, sr=sr)
            X.append(feat_vec)
            y_true.append(1) # Fake
            fake_count += 1
        except Exception as e:
            print(f"Skipping {os.path.basename(file)}: {e}")

    if not X:
        print("\nNo audio files found. Please put some .wav or .mp3 files in data/manual_test/real/ and data/manual_test/fake/")
        return

    print(f"\n[3] Evaluating Conformer Model on {real_count + fake_count} total clips...")
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
        preds = torch.argmax(logits, dim=1).cpu().numpy()

    acc = accuracy_score(y_true, preds)
    prec = precision_score(y_true, preds, zero_division=0)
    rec = recall_score(y_true, preds, zero_division=0)
    f1 = f1_score(y_true, preds, zero_division=0)
    cm = confusion_matrix(y_true, preds, labels=[0, 1])

    print("\n" + "=" * 50)
    print("📈 MANUAL OOD EVALUATION RESULTS")
    print("=" * 50)
    print(f"Accuracy         : {acc * 100:.2f}%")
    print(f"Precision        : {prec * 100:.2f}%")
    print(f"Recall           : {rec * 100:.2f}%")
    print(f"F1-Score         : {f1 * 100:.2f}%")
    print("\nConfusion Matrix [TN FP / FN TP]:")
    print(cm)
    
    tn, fp, fn, tp = cm.ravel()
    print("\nBreakdown Analysis:")
    if real_count > 0:
        print(f"- Correctly identified {tn}/{real_count} Real Human Voices.")
    if fake_count > 0:
        print(f"- Correctly identified {tp}/{fake_count} AI-Generated Voices.")

if __name__ == "__main__":
    evaluate_manual_directory()
