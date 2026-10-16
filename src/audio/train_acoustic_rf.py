import os
import sys
import joblib
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import numpy as np
import librosa
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_curve
from sklearn.preprocessing import StandardScaler
from torchaudio.models import Conformer

from src.data.dataset_loader import prepare_phase1_dataset
from src.audio.feature_extractor import extract_acoustic_features

def compute_eer(y_true, y_scores):
    fpr, tpr, thresholds = roc_curve(y_true, y_scores, pos_label=1)
    fnr = 1 - tpr
    eer_idx = np.nanargmin(np.abs(fpr - fnr))
    eer = float((fpr[eer_idx] + fnr[eer_idx]) / 2.0)
    eer_threshold = float(thresholds[eer_idx])
    return eer, eer_threshold

class AcousticConformer(nn.Module):
    """
    Multi-Head Conformer Neural Architecture for Forensic Deepfake Detection.
    Combines self-attention with depthwise separable convolutions to capture
    both long-range vocal cadence and short-term vocoder artifacts.
    """
    def __init__(self, input_dim=400, seq_len=16, conformer_dim=64):
        super().__init__()
        self.seq_len = seq_len
        self.conformer_dim = conformer_dim
        
        # Layer normalization & projection
        self.input_norm = nn.LayerNorm(input_dim)
        self.feature_projection = nn.Sequential(
            nn.Linear(input_dim, seq_len * conformer_dim),
            nn.GELU(),
            nn.Dropout(0.15)
        )
        
        # 2-Layer Conformer
        self.conformer = Conformer(
            input_dim=conformer_dim,
            num_heads=4,
            ffn_dim=128,
            num_layers=2,
            depthwise_conv_kernel_size=5,
            dropout=0.15
        )
        
        # Attentive sequence pooling
        self.attention_pool = nn.Sequential(
            nn.Linear(conformer_dim, 1),
            nn.Softmax(dim=1)
        )
        
        # Classification Head
        self.classifier = nn.Sequential(
            nn.Linear(conformer_dim, 64),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.GELU(),
            nn.Linear(32, 2)
        )

    def forward(self, x):
        batch_size = x.size(0)
        x_norm = self.input_norm(x)
        x_proj = self.feature_projection(x_norm)
        x_seq = x_proj.view(batch_size, self.seq_len, self.conformer_dim)
        
        lengths = torch.full((batch_size,), self.seq_len, dtype=torch.long, device=x.device)
        out, _ = self.conformer(x_seq, lengths)
        
        # Attentive pooling
        attn_weights = self.attention_pool(out)
        pooled = torch.sum(out * attn_weights, dim=1)
        
        logits = self.classifier(pooled)
        return logits

    def predict_proba(self, X):
        self.eval()
        device = next(self.parameters()).device
        if isinstance(X, np.ndarray):
            X_tensor = torch.tensor(X, dtype=torch.float32).to(device)
        elif isinstance(X, torch.Tensor):
            X_tensor = X.to(device)
        else:
            X_tensor = torch.tensor(np.array(X), dtype=torch.float32).to(device)
        with torch.no_grad():
            logits = self.forward(X_tensor)
            probs = torch.softmax(logits, dim=1).cpu().numpy()
        return probs

    def predict(self, X):
        probs = self.predict_proba(X)
        return np.argmax(probs, axis=1)

def run_phase1_baseline():
    print("=" * 70)
    print("PHASE 1: DEEPGUARD CONFORMER NEURAL NETWORK TRAINING")
    print("=" * 70)

    # 1. Prepare / Load Dataset
    reals, fakes = prepare_phase1_dataset()
    print(f"Loaded {len(reals)} Real (Human) and {len(fakes)} Fake (AI/TTS) clips.")

    X, y = [], []
    feature_names = None

    print("\nExtracting acoustic features...")
    for filepath in reals:
        audio, sr = librosa.load(filepath, sr=16000)
        vec, names = extract_acoustic_features(audio, sr=sr)
        X.append(vec)
        y.append(0)
        if feature_names is None: feature_names = names

    for filepath in fakes:
        audio, sr = librosa.load(filepath, sr=16000)
        vec, names = extract_acoustic_features(audio, sr=sr)
        X.append(vec)
        y.append(1)

    X = np.array(X)
    y = np.array(y)
    
    # 2. Train / Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # 3. Scale Features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 4. Convert to PyTorch Tensors
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"\nTraining on device: {device}")
    
    X_train_tensor = torch.tensor(X_train_scaled, dtype=torch.float32)
    y_train_tensor = torch.tensor(y_train, dtype=torch.long)
    X_test_tensor = torch.tensor(X_test_scaled, dtype=torch.float32).to(device)
    
    train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

    # 5. Initialize Conformer Model
    input_dim = X.shape[1]
    model = AcousticConformer(input_dim=input_dim).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # 6. Training Loop
    epochs = 10
    print(f"Training Conformer for {epochs} epochs...")
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        if (epoch+1) % 5 == 0:
            print(f"  Epoch [{epoch+1}/{epochs}], Loss: {total_loss/len(train_loader):.4f}")

    # 7. Evaluate
    model.eval()
    with torch.no_grad():
        test_outputs = model(X_test_tensor)
        test_probs = torch.softmax(test_outputs, dim=1)[:, 1].cpu().numpy()
        test_preds = torch.argmax(test_outputs, dim=1).cpu().numpy()

    acc = accuracy_score(y_test, test_preds)
    prec = precision_score(y_test, test_preds, zero_division=0)
    rec = recall_score(y_test, test_preds, zero_division=0)
    f1 = f1_score(y_test, test_preds, zero_division=0)
    cm = confusion_matrix(y_test, test_preds)
    eer, eer_thresh = compute_eer(y_test, test_probs)

    print("\n" + "=" * 50)
    print("📈 PHASE 1 CONFORMER EVALUATION RESULTS")
    print("=" * 50)
    print(f"Accuracy         : {acc * 100:.2f}%")
    print(f"Precision        : {prec * 100:.2f}%")
    print(f"Recall           : {rec * 100:.2f}%")
    print(f"F1-Score         : {f1 * 100:.2f}%")
    print(f"Equal Error Rate : {eer * 100:.2f}%")

    # 8. Save artifacts
    models_dir = os.path.join(PROJECT_ROOT, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    scaler_path = os.path.join(models_dir, "scaler.pkl")
    model_path = os.path.join(models_dir, "conformer_model.pth")
    
    joblib.dump(scaler, scaler_path)
    torch.save(model.state_dict(), model_path)
    
    print(f"\nSaved Conformer weights to {model_path}")

    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "eer": eer,
        "model": model,
        "model_path": model_path,
        "scaler": scaler
    }

if __name__ == "__main__":
    run_phase1_baseline()
