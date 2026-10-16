import os
import sys
import torch
import numpy as np
import io
import soundfile as sf
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

def evaluate_on_sounds():
    print("======================================================================")
    print("PHASE 1: OUT-OF-DISTRIBUTION EVALUATION (AI MUSIC vs REAL SOUNDS)")
    print("======================================================================")
    
    analyzer = AcousticAnalyzer(model_path="models/conformer_model.pth", scaler_path="models/scaler.pkl")
    
    X = []
    y_true = []
    
    print("\n[1] Downloading Real Environmental Sounds (ESC-50)...")
    try:
        real_ds = load_dataset("ashraq/esc50", split="train")
        real_ds = real_ds.cast_column("audio", Audio(decode=False))
        
        count = 0
        for item in real_ds:
            if count >= 50:
                break
            
            try:
                audio_bytes = item["audio"]["bytes"]
                audio_array, sr = sf.read(io.BytesIO(audio_bytes))
                # Truncate to 3 seconds for consistency
                if len(audio_array) > sr * 3:
                    audio_array = audio_array[:sr * 3]
                    
                feat_vec, _ = extract_acoustic_features(audio_array, sr=sr)
                X.append(feat_vec)
                y_true.append(0) # Real
                count += 1
            except Exception as e:
                continue
        print(f"Loaded {count} Real environmental sound clips.")
    except Exception as e:
        print(f"Failed to load Real sounds: {e}")

    print("\n[2] Downloading AI-Generated Music (Suno AI)...")
    import urllib.request
    import librosa
    try:
        # Using a dataset of AI generated music
        fake_ds = load_dataset("Kukedlc/suno-ai-music-dataset", split="train")
        
        count = 0
        for item in fake_ds:
            if count >= 50:
                break
            try:
                url = item.get("audio_url")
                if not url: continue
                
                temp_file = f"temp_suno_{count}.mp3"
                urllib.request.urlretrieve(url, temp_file)
                
                audio_array, sr = librosa.load(temp_file, sr=16000)
                
                # Truncate to 3 seconds for consistency
                if len(audio_array) > sr * 3:
                    audio_array = audio_array[:sr * 3]
                    
                feat_vec, _ = extract_acoustic_features(audio_array, sr=sr)
                X.append(feat_vec)
                y_true.append(1) # Fake
                count += 1
                
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                continue
        print(f"Loaded {count} AI-Generated music clips.")
    except Exception as e:
        print(f"Failed to load AI sounds: {e}")

    if not X:
        print("No data loaded. Exiting.")
        return

    print("\n[3] Evaluating Conformer Model on OOD Data...")
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
    print("📈 OUT-OF-DISTRIBUTION EVALUATION RESULTS")
    print("=" * 50)
    print(f"Dataset          : ESC-50 (Real Sounds) vs Suno AI (Fake Music)")
    print(f"Accuracy         : {acc * 100:.2f}%")
    print(f"Precision        : {prec * 100:.2f}%")
    print(f"Recall           : {rec * 100:.2f}%")
    print(f"F1-Score         : {f1 * 100:.2f}%")
    print("\nConfusion Matrix [TN FP / FN TP]:")
    print(cm)

if __name__ == "__main__":
    evaluate_on_sounds()
