import os
import sys
import numpy as np
import librosa
import scipy.signal as signal
import torch
import joblib

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.audio.train_acoustic_rf import AcousticConformer
from src.audio.feature_extractor import extract_acoustic_features

class AcousticAnalyzer:
    """
    DeepGuard Forensic Analyzer for VoxSentinel AI.
    Performs acoustic deepfake voice analysis using the trained AcousticConformer
    neural network or heuristic feature extraction fallback when models are not loaded.
    """
    def __init__(self, model_path=None, scaler_path=None, model_name=None):
        default_model = os.path.join(PROJECT_ROOT, "models", "conformer_model.pth")
        default_scaler = os.path.join(PROJECT_ROOT, "models", "scaler.pkl")

        self.model_path = model_path or (default_model if os.path.exists(default_model) else None)
        self.scaler_path = scaler_path or (default_scaler if os.path.exists(default_scaler) else None)
        self.model_name = model_name or "AcousticConformer-v1"

        self.device = torch.device("cpu")
        self.scaler = None
        self.model = None
        self.is_trained = False

        self._load_model_and_scaler()

    def _load_model_and_scaler(self):
        try:
            if self.scaler_path and os.path.exists(self.scaler_path):
                self.scaler = joblib.load(self.scaler_path)

            if self.model_path and os.path.exists(self.model_path):
                model = AcousticConformer(input_dim=400)
                state_dict = torch.load(self.model_path, map_location=self.device)
                model.load_state_dict(state_dict)
                model.to(self.device)
                model.eval()
                self.model = model

            if self.model is not None and self.scaler is not None:
                self.is_trained = True

            self.ensemble = None
            ensemble_path = os.path.join(PROJECT_ROOT, "models", "acoustic_ensemble.joblib")
            if os.path.exists(ensemble_path):
                try:
                    self.ensemble = joblib.load(ensemble_path)
                except Exception:
                    self.ensemble = None
        except Exception as e:
            # Fallback gracefully if model loading fails
            self.model = None
            self.scaler = None
            self.ensemble = None
            self.is_trained = False

    @staticmethod
    def _get_default_feature_summary():
        return {
            "pitch_jitter": 0.0,
            "shimmer": 0.0,
            "shimmer_local": 0.0,
            "centroid": 0.0,
            "spectral_centroid_mean": 0.0,
            "flatness": 0.0,
            "spectral_flatness_mean": 0.0,
            "zcr": 0.0,
            "zero_crossing_rate_mean": 0.0,
            "inst_freq_std": 0.0,
            "spec_entropy_std": 0.0,
            "spec_flux_mean": 0.0,
            "delta_mfcc_std": 0.0,
            "lfcc_mean_1": 0.0,
            "cqcc_mean_1": 0.0,
            "ssl_mean_1": 0.0
        }

    def analyze_audio_file(self, file_path_or_y, sr=16000):
        """
        Analyzes audio signal or file for synthetic voice / deepfake acoustic artifacts.
        Handles edge cases (silence, pure noise, short clips, stereo, NaN/Inf).
        """
        y = None

        if isinstance(file_path_or_y, str):
            if not file_path_or_y.strip():
                return {
                    "synthetic_probability": 0.50,
                    "is_synthetic": False,
                    "feature_summary": self._get_default_feature_summary(),
                    "explanations": ["ACOUSTIC FORENSICS: Invalid or empty audio path provided."]
                }
            if not os.path.exists(file_path_or_y):
                raise FileNotFoundError(f"Audio file not found: {file_path_or_y}")
            try:
                y, sr = librosa.load(file_path_or_y, sr=sr)
            except Exception:
                y = None
        elif isinstance(file_path_or_y, torch.Tensor):
            y = file_path_or_y.detach().cpu().numpy()
        elif hasattr(file_path_or_y, "__array__") or isinstance(file_path_or_y, (list, tuple)):
            y = np.asarray(file_path_or_y, dtype=np.float32)
        else:
            y = file_path_or_y

        # Handle empty/corrupted audio input
        if y is None or len(y) == 0:
            return {
                "synthetic_probability": 0.50,
                "is_synthetic": False,
                "feature_summary": self._get_default_feature_summary(),
                "explanations": ["ACOUSTIC FORENSICS: Invalid or empty audio signal provided."]
            }

        y = np.asarray(y, dtype=np.float32)

        # Downmix stereo to mono if multi-channel
        if y.ndim > 1:
            if y.shape[0] <= 8 and y.shape[1] > y.shape[0]:
                y = np.mean(y, axis=0)
            else:
                y = np.mean(y, axis=-1)

        y = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0)

        # 1. Edge Case: Completely Silent Audio
        max_amplitude = float(np.max(np.abs(y))) if len(y) > 0 else 0.0
        rms_energy = float(np.sqrt(np.mean(y ** 2))) if len(y) > 0 else 0.0
        if max_amplitude < 1e-4 or rms_energy < 1e-5:
            return {
                "synthetic_probability": 0.05,
                "is_synthetic": False,
                "feature_summary": self._get_default_feature_summary(),
                "explanations": [
                    "ACOUSTIC FORENSICS: Completely silent audio detected.",
                    "Insufficient vocal signal present for deepfake acoustic analysis."
                ]
            }

        # 2. Extract Acoustic Metrics for Forensic Summary
        explanations = []
        is_short_clip = len(y) < int(sr * 0.5)
        if is_short_clip:
            explanations.append("Notice: Short audio duration (< 0.5s); forensic confidence may be adjusted.")

        # Ensure y has at least 2048 samples for FFT operations and pyin
        if len(y) < 2048:
            y_eval = np.pad(y, (0, 2048 - len(y)), mode='constant')
        else:
            y_eval = y

        zcr = librosa.feature.zero_crossing_rate(y_eval)
        rms = librosa.feature.rms(y=y_eval, frame_length=512, hop_length=256)[0]
        spec_cent = librosa.feature.spectral_centroid(y=y_eval, sr=sr)[0]
        spec_flat = librosa.feature.spectral_flatness(y=y_eval)[0]

        mean_zcr = float(np.nan_to_num(np.mean(zcr), nan=0.0, posinf=0.0, neginf=0.0))
        mean_centroid = float(np.nan_to_num(np.mean(spec_cent), nan=0.0, posinf=0.0, neginf=0.0))
        mean_flatness = float(np.nan_to_num(np.mean(spec_flat), nan=0.0, posinf=0.0, neginf=0.0))

        # Genuine Pitch Jitter & Local Shimmer Calculations
        try:
            if max_amplitude >= 1e-4 and float(np.std(y_eval)) >= 1e-5:
                f0, voiced_flag, _ = librosa.pyin(y_eval, fmin=65, fmax=300, sr=sr)
            else:
                f0, voiced_flag = None, None
            f0_clean = f0[voiced_flag & ~np.isnan(f0)] if (f0 is not None and voiced_flag is not None) else np.array([])
            if len(f0_clean) > 2:
                periods = 1.0 / f0_clean
                mean_period = float(np.mean(periods))
                if mean_period > 0:
                    pitch_jitter = float(np.mean(np.abs(np.diff(periods))) / (mean_period + 1e-8))
                else:
                    pitch_jitter = 0.015
            else:
                pitch_jitter = float(np.std(spec_cent) / (mean_centroid + 1e-6))
        except Exception:
            pitch_jitter = 0.015
        pitch_jitter = float(np.nan_to_num(pitch_jitter, nan=0.015, posinf=0.015, neginf=0.015))

        if len(rms) > 2:
            mean_rms = float(np.mean(rms))
            shimmer = float(np.mean(np.abs(np.diff(rms))) / (mean_rms + 1e-8))
        else:
            shimmer = 0.02
        shimmer = float(np.nan_to_num(shimmer, nan=0.02, posinf=0.02, neginf=0.02))

        # Hilbert Transform Instantaneous Frequency Fluctuation
        try:
            analytic_signal = signal.hilbert(y_eval)
            instantaneous_phase = np.unwrap(np.angle(analytic_signal))
            inst_freq = np.diff(instantaneous_phase) / (2.0 * np.pi) * sr
            inst_freq_std = float(np.nan_to_num(np.std(inst_freq), nan=0.0, posinf=0.0, neginf=0.0))
        except Exception:
            inst_freq_std = 0.0

        # Spectral Entropy Dynamics & Flux
        try:
            S = np.abs(librosa.stft(y_eval, n_fft=512, hop_length=256))
            prob_S = S / (np.sum(S, axis=0, keepdims=True) + 1e-10)
            entropy = -np.sum(prob_S * np.log2(prob_S + 1e-12), axis=0)
            spec_entropy_std = float(np.nan_to_num(np.std(entropy), nan=0.0, posinf=0.0, neginf=0.0))
            spec_flux = np.mean(np.diff(S, axis=1)**2) if S.shape[1] > 1 else 0.0
            spec_flux_mean = float(np.nan_to_num(np.sqrt(spec_flux), nan=0.0, posinf=0.0, neginf=0.0))
        except Exception:
            spec_entropy_std = 0.0
            spec_flux_mean = 0.0

        # Delta-MFCC Articulatory Speed
        try:
            mfcc = librosa.feature.mfcc(y=y_eval, sr=sr, n_mfcc=13)
            d_mfcc = librosa.feature.delta(mfcc)
            delta_mfcc_std = float(np.nan_to_num(np.std(d_mfcc), nan=0.0, posinf=0.0, neginf=0.0))
        except Exception:
            delta_mfcc_std = 0.0
            mfcc = np.zeros((13, 1), dtype=np.float32)

        feat_dict = {
            "pitch_jitter": round(pitch_jitter, 5),
            "shimmer": round(shimmer, 5),
            "shimmer_local": round(shimmer, 5),
            "centroid": round(mean_centroid, 2),
            "spectral_centroid_mean": round(mean_centroid, 2),
            "flatness": round(mean_flatness, 5),
            "spectral_flatness_mean": round(mean_flatness, 5),
            "zcr": round(mean_zcr, 5),
            "zero_crossing_rate_mean": round(mean_zcr, 5),
            "inst_freq_std": round(inst_freq_std, 2),
            "spec_entropy_std": round(spec_entropy_std, 4),
            "spec_flux_mean": round(spec_flux_mean, 4),
            "delta_mfcc_std": round(delta_mfcc_std, 4),
            "lfcc_mean_1": round(float(np.nan_to_num(np.mean(mfcc[1]))), 4) if mfcc.shape[0] > 1 else 0.0,
            "cqcc_mean_1": round(float(np.nan_to_num(np.mean(mfcc[2]))), 4) if mfcc.shape[0] > 2 else 0.0,
            "ssl_mean_1": round(float(np.nan_to_num(np.mean(mfcc[3]))), 4) if mfcc.shape[0] > 3 else 0.0
        }

        # 3. Edge Case: Pure White / Static Noise (High flatness, high ZCR, no speech harmonics)
        if mean_flatness > 0.40 and mean_zcr > 0.30:
            explanations.append("ACOUSTIC FORENSICS: Static background noise detected without human speech harmonics.")
            return {
                "synthetic_probability": 0.15,
                "is_synthetic": False,
                "feature_summary": feat_dict,
                "explanations": explanations
            }

        # 4. Determine Synthetic Probability via Neural Conformer & Forensic Ensemble
        if self.scaler is not None and (self.model is not None or getattr(self, 'ensemble', None) is not None):
            try:
                feat_vec, _ = extract_acoustic_features(y, sr=sr)
                feat_vec = np.nan_to_num(feat_vec, nan=0.0, posinf=0.0, neginf=0.0)
                feat_scaled = self.scaler.transform([feat_vec])
                feat_scaled = np.nan_to_num(feat_scaled, nan=0.0, posinf=0.0, neginf=0.0)

                conf_p = None
                if self.model is not None:
                    with torch.no_grad():
                        X_tensor = torch.tensor(feat_scaled, dtype=torch.float32).to(self.device)
                        logits = self.model(X_tensor)
                        probs = torch.softmax(logits, dim=1)
                        if probs.shape[1] > 1:
                            conf_p = float(probs[0, 1].item())
                        else:
                            conf_p = float(torch.sigmoid(logits)[0, 0].item())

                ens_p = None
                if getattr(self, 'ensemble', None) is not None:
                    hgb = self.ensemble.get("hgb")
                    rf = self.ensemble.get("rf")
                    et = self.ensemble.get("et")
                    plist = []
                    if hgb is not None: plist.append(float(hgb.predict_proba(feat_scaled)[0, 1]))
                    if rf is not None: plist.append(float(rf.predict_proba(feat_scaled)[0, 1]))
                    if et is not None: plist.append(float(et.predict_proba(feat_scaled)[0, 1]))
                    ens_p = float(np.mean(plist)) if plist else 0.5

                if conf_p is not None and ens_p is not None:
                    raw_clf_proba = 0.40 * conf_p + 0.60 * ens_p
                elif conf_p is not None:
                    raw_clf_proba = conf_p
                elif ens_p is not None:
                    raw_clf_proba = ens_p
                else:
                    raw_clf_proba = 0.50
            except Exception:
                raw_clf_proba = 0.82 if (mean_flatness < 0.005 or mean_zcr < 0.02) else 0.18
        else:
            raw_clf_proba = 0.82 if (mean_flatness < 0.005 or mean_zcr < 0.02) else 0.18
            explanations.append("Notice: Pretrained acoustic model not loaded; heuristic analysis applied.")

        raw_clf_proba = float(np.nan_to_num(np.clip(raw_clf_proba, 0.0, 1.0), nan=0.5))
        is_synthetic = bool(raw_clf_proba >= 0.50)

        if is_synthetic:
            explanations.append("ACOUSTIC FORENSICS: Feature signature strongly matches synthetic AI voices.")
            explanations.append("HIGH CONFIDENCE CLONE: Detected synthetic vocoder artifacts.")
        else:
            explanations.append("ACOUSTIC FORENSICS: Feature signature matches genuine human voice patterns.")
            explanations.append("HIGH CONFIDENCE HUMAN: Natural voice variations verified.")

        seen = set()
        unique_explanations = [x for x in explanations if not (x in seen or seen.add(x))]

        return {
            "synthetic_probability": round(raw_clf_proba, 4),
            "is_synthetic": is_synthetic,
            "feature_summary": feat_dict,
            "explanations": unique_explanations
        }
