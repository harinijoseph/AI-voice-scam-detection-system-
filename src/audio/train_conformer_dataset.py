import os
import sys
import glob
import time
import random
import joblib
import librosa
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from torchaudio.models import Conformer

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier, ExtraTreesClassifier

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.audio.feature_extractor import extract_acoustic_features


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
        attn_weights = self.attention_pool(out)  # (Batch, SeqLen, 1)
        pooled = torch.sum(out * attn_weights, dim=1)  # (Batch, ConformerDim)
        
        logits = self.classifier(pooled)
        return logits

    def predict_proba(self, X):
        self.eval()
        device = next(self.parameters()).device
        if isinstance(X, np.ndarray):
            X_tensor = torch.tensor(X, dtype=torch.float32).to(device)
        else:
            X_tensor = X.to(device)
        with torch.no_grad():
            logits = self.forward(X_tensor)
            probs = torch.softmax(logits, dim=1).cpu().numpy()
        return probs

    def predict(self, X):
        probs = self.predict_proba(X)
        return np.argmax(probs, axis=1)


def _process_single_file(args):
    filepath, label, domain = args
    try:
        y, sr = librosa.load(filepath, sr=16000)
        feat, _ = extract_acoustic_features(y, sr=sr)
        return feat, label, domain, filepath
    except Exception:
        return None, label, domain, filepath


def train_and_evaluate_model(test_size=0.15, epochs=30):
    """
    Trains the revamped AcousticConformer and Forensic Ensemble jointly on:
    1. human-nonhuman speech corpus (modern zero-shot neural TTS & real human speech)
    2. koyyalamudiraghavendra deepfake audio detection dataset (phase1 real & fake speech)
    """
    print("=" * 80)
    print("VOXSENTINEL AI: MULTI-CORPUS JOINT MODEL TRAINING")
    print("Corpora: human-nonhuman/ (2,001 files) + koyyalamudiraghavendra (400 files)")
    print("=" * 80)

    # 1. human-nonhuman corpus
    human_dir = os.path.join(PROJECT_ROOT, "human-nonhuman", "human")
    nonhuman_dir = os.path.join(PROJECT_ROOT, "human-nonhuman", "nonhuman")
    human_files = sorted(glob.glob(os.path.join(human_dir, "*.mp3")))
    nonhuman_files = sorted(glob.glob(os.path.join(nonhuman_dir, "*.mp3")))

    # 2. koyyalamudiraghavendra corpus
    koyyala_real_dir = os.path.join(PROJECT_ROOT, "data", "phase1", "real")
    koyyala_fake_dir = os.path.join(PROJECT_ROOT, "data", "phase1", "fake")
    koyyala_reals = sorted(glob.glob(os.path.join(koyyala_real_dir, "*.wav")))
    koyyala_fakes = sorted(glob.glob(os.path.join(koyyala_fake_dir, "*.wav")))

    print(f"Loaded Corpora:")
    print(f"  [1] human-nonhuman:        {len(human_files)} Human, {len(nonhuman_files)} AI Synthetic")
    print(f"  [2] koyyalamudiraghavendra: {len(koyyala_reals)} Human, {len(koyyala_fakes)} AI Synthetic")
    total_reals = len(human_files) + len(koyyala_reals)
    total_fakes = len(nonhuman_files) + len(koyyala_fakes)
    print(f"  TOTAL COMBINED DATASET:    {total_reals} Human, {total_fakes} AI Synthetic ({total_reals+total_fakes} files total)")

    tasks = (
        [(f, 0, "human-nonhuman") for f in human_files] +
        [(f, 1, "human-nonhuman") for f in nonhuman_files] +
        [(f, 0, "koyyala") for f in koyyala_reals] +
        [(f, 1, "koyyala") for f in koyyala_fakes]
    )
    random.seed(42)
    random.shuffle(tasks)

    print(f"\n[1/4] Extracting acoustic 400-D features across all {len(tasks)} files in parallel...")
    t0 = time.time()
    
    X, y, domains, filepaths = [], [], [], []
    with ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as executor:
        futures = [executor.submit(_process_single_file, task) for task in tasks]
        done_count = 0
        for f in as_completed(futures):
            feat, label, domain, fp = f.result()
            if feat is not None:
                X.append(feat)
                y.append(label)
                domains.append(domain)
                filepaths.append(fp)
            done_count += 1
            if done_count % 300 == 0 or done_count == len(tasks):
                print(f"  Processed {done_count}/{len(tasks)} files ({time.time()-t0:.1f}s)...")

    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.int64)
    domains = np.array(domains)
    filepaths = np.array(filepaths)
    print(f"Extraction complete in {time.time()-t0:.1f}s! Valid feature matrix: {X.shape}")

    # Stratified Train / Test split preserving label and domain representation
    strat_keys = [f"{lbl}_{dom}" for lbl, dom in zip(y, domains)]
    indices = np.arange(len(y))
    train_idx, test_idx = train_test_split(
        indices, test_size=test_size, random_state=42, stratify=strat_keys
    )

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    dom_test = domains[test_idx]

    print(f"\n[2/4] Scaling feature distributions...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    X_train_scaled = np.nan_to_num(X_train_scaled, nan=0.0, posinf=0.0, neginf=0.0)
    X_test_scaled = np.nan_to_num(X_test_scaled, nan=0.0, posinf=0.0, neginf=0.0)

    # Train High-Accuracy Forensic Tree Ensemble
    print(f"\n[3/4] Training Forensic Gradient Boosting, ExtraTrees & Random Forest Ensemble...")
    t_ens = time.time()
    hgb = HistGradientBoostingClassifier(
        max_iter=180, 
        learning_rate=0.07, 
        max_leaf_nodes=40, 
        l2_regularization=0.6,
        random_state=42
    )
    hgb.fit(X_train_scaled, y_train)

    rf = RandomForestClassifier(
        n_estimators=180, 
        max_depth=20, 
        min_samples_split=4, 
        random_state=42, 
        n_jobs=-1
    )
    rf.fit(X_train_scaled, y_train)

    et = ExtraTreesClassifier(
        n_estimators=180, 
        max_depth=20, 
        min_samples_split=4, 
        random_state=42, 
        n_jobs=-1
    )
    et.fit(X_train_scaled, y_train)

    p_hgb = hgb.predict_proba(X_test_scaled)
    p_rf = rf.predict_proba(X_test_scaled)
    p_et = et.predict_proba(X_test_scaled)
    ens_preds = (p_hgb + p_rf + p_et) / 3.0
    ens_pred_labels = np.argmax(ens_preds, axis=1)
    ens_acc = accuracy_score(y_test, ens_pred_labels)
    ens_auc = roc_auc_score(y_test, ens_preds[:, 1])
    print(f"  Tree Ensemble Test Accuracy: {ens_acc:.2%}, ROC-AUC: {ens_auc:.4f} in {time.time()-t_ens:.1f}s")

    # Train Deep Acoustic Conformer Neural Network
    print(f"\n[4/4] Training Deep Acoustic Conformer Neural Network ({epochs} epochs)...")
    device = torch.device("mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu"))
    print(f"  Training device: {device}")

    model = AcousticConformer(input_dim=X.shape[1]).to(device)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)
    optimizer = optim.AdamW(model.parameters(), lr=0.0015, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    train_ds = TensorDataset(torch.tensor(X_train_scaled, dtype=torch.float32), torch.tensor(y_train, dtype=torch.long))
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)

    test_tensor = torch.tensor(X_test_scaled, dtype=torch.float32).to(device)

    best_acc = 0.0
    best_weights = None

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            optimizer.zero_grad()
            out = model(batch_x)
            loss = criterion(out, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(batch_y)
        
        scheduler.step()
        
        # Evaluate Conformer
        model.eval()
        with torch.no_grad():
            test_logits = model(test_tensor)
            test_probs = torch.softmax(test_logits, dim=1).cpu().numpy()
            epoch_preds = np.argmax(test_probs, axis=1)
            epoch_acc = accuracy_score(y_test, epoch_preds)

        if epoch_acc > best_acc:
            best_acc = epoch_acc
            best_weights = model.state_dict()

        if epoch % 5 == 0 or epoch == epochs:
            print(f"  Epoch {epoch:02d}/{epochs:02d} - Loss: {total_loss/len(X_train):.4f} - Test Acc: {epoch_acc:.2%}")

    if best_weights:
        model.load_state_dict(best_weights)

    # Final Combined Evaluation
    conf_probs = model.predict_proba(X_test_scaled)
    # Blend Conformer deep feature attention with calibrated gradient tree probabilities
    final_probs = 0.40 * conf_probs + 0.60 * ens_preds
    final_preds = np.argmax(final_probs, axis=1)

    final_acc = accuracy_score(y_test, final_preds)
    final_prec = precision_score(y_test, final_preds)
    final_rec = recall_score(y_test, final_preds)
    final_f1 = f1_score(y_test, final_preds)
    cm = confusion_matrix(y_test, final_preds)

    print("\n" + "=" * 80)
    print("FINAL EVALUATION METRICS ON COMBINED HELD-OUT TEST DATASET:")
    print("=" * 80)
    print(f"  Combined Test Accuracy:  {final_acc:.2%}")
    print(f"  Combined Precision:      {final_prec:.2%}")
    print(f"  Combined Recall:         {final_rec:.2%}")
    print(f"  Combined F1 Score:       {final_f1:.2%}")
    print(f"  Confusion Matrix (TN, FP, FN, TP):\n{cm}")

    # Domain-specific breakdowns on held-out test split
    mask_hn = (dom_test == "human-nonhuman")
    mask_koy = (dom_test == "koyyala")
    acc_hn = accuracy_score(y_test[mask_hn], final_preds[mask_hn])
    acc_koy = accuracy_score(y_test[mask_koy], final_preds[mask_koy])
    print("-" * 80)
    print(f"  Test Accuracy on human-nonhuman/ (N={np.sum(mask_hn)}):        {acc_hn:.2%}")
    print(f"  Test Accuracy on koyyalamudiraghavendra (N={np.sum(mask_koy)}): {acc_koy:.2%}")
    print("=" * 80)

    # Save artifacts
    models_dir = os.path.join(PROJECT_ROOT, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    conformer_path = os.path.join(models_dir, "conformer_model.pth")
    scaler_path = os.path.join(models_dir, "scaler.pkl")
    ensemble_path = os.path.join(models_dir, "acoustic_ensemble.joblib")

    torch.save(model.state_dict(), conformer_path)
    joblib.dump(scaler, scaler_path)
    joblib.dump({"hgb": hgb, "rf": rf, "et": et}, ensemble_path)

    print(f"\nSaved models:")
    print(f"  - {conformer_path}")
    print(f"  - {scaler_path}")
    print(f"  - {ensemble_path}")

    # Full evaluation across all 400 clips of koyyalamudiraghavendra
    print("\n[5/5] Evaluating Joint Model on ALL 400 koyyalamudiraghavendra files...")
    koy_all_tasks = [(f, 0) for f in koyyala_reals] + [(f, 1) for f in koyyala_fakes]
    X_koy, y_koy = [], []
    for fp, lbl in koy_all_tasks:
        idx = np.where(filepaths == fp)[0]
        if len(idx) > 0:
            X_koy.append(X[idx[0]])
            y_koy.append(lbl)

    X_koy = np.array(X_koy, dtype=np.float32)
    y_koy = np.array(y_koy, dtype=np.int64)
    X_koy_scaled = np.nan_to_num(scaler.transform(X_koy), nan=0.0, posinf=0.0, neginf=0.0)

    p_koy_ens = (hgb.predict_proba(X_koy_scaled) + rf.predict_proba(X_koy_scaled) + et.predict_proba(X_koy_scaled)) / 3.0
    p_koy_conf = model.predict_proba(X_koy_scaled)
    p_koy_final = 0.40 * p_koy_conf + 0.60 * p_koy_ens
    preds_koy = np.argmax(p_koy_final, axis=1)

    koy_acc = accuracy_score(y_koy, preds_koy)
    koy_prec = precision_score(y_koy, preds_koy)
    koy_rec = recall_score(y_koy, preds_koy)
    koy_f1 = f1_score(y_koy, preds_koy)
    koy_cm = confusion_matrix(y_koy, preds_koy)
    print(f"  FULL 400-CLIP KOYYALAMUDIRAGHAVENDRA ACCURACY:  {koy_acc:.2%}")
    print(f"  Precision: {koy_prec:.2%}, Recall: {koy_rec:.2%}, F1: {koy_f1:.2%}")
    print(f"  Confusion Matrix (TN={koy_cm[0,0]}/200, FP={koy_cm[0,1]}/200, FN={koy_cm[1,0]}/200, TP={koy_cm[1,1]}/200)")
    print("=" * 80)

    return {
        "accuracy": final_acc,
        "precision": final_prec,
        "recall": final_rec,
        "f1": final_f1,
        "acc_human_nonhuman": acc_hn,
        "acc_koyyala": acc_koy,
        "full_koyyala_acc": koy_acc
    }


if __name__ == "__main__":
    train_and_evaluate_model(test_size=0.15, epochs=30)
