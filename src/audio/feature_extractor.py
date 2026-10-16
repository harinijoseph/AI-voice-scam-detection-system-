import numpy as np
import librosa

SAMPLE_RATE = 16000
DURATION = 4
N_MFCC = 40
N_MELS = 128

def extract_acoustic_features(y, sr=None):
    """
    DeepGuard Feature Extraction Pipeline (approx. 400 Features).
    Matches exactly the feature extraction used in the DeepGuard project.
    
    Expects y (audio time series). It resamples to SAMPLE_RATE if needed, 
    and pads/truncates to DURATION.
    """
    if y is None:
        raise ValueError("Audio vector is None.")
    
    y = np.asarray(y, dtype=np.float32)
    if y.size == 0:
        raise ValueError("Audio vector is empty.")

    # Downmix multi-channel (stereo) audio to mono
    if y.ndim > 1:
        # If shape is (channels, samples) where channels <= 8
        if y.shape[0] <= 8 and y.shape[1] > y.shape[0]:
            y = np.mean(y, axis=0)
        else:
            y = np.mean(y, axis=-1)

    y = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0)

    # Resample if sr is provided and different from SAMPLE_RATE
    if sr is not None and sr != SAMPLE_RATE:
        y = librosa.resample(y, orig_sr=sr, target_sr=SAMPLE_RATE)
        
    sr = SAMPLE_RATE

    # Trim leading and trailing dead air / silence so features capture active speech physics
    try:
        y_trimmed, _ = librosa.effects.trim(y, top_db=25)
        if len(y_trimmed) >= int(SAMPLE_RATE * 0.5):
            y = y_trimmed
    except Exception:
        pass

    DURATION = 8
    target_len = SAMPLE_RATE * DURATION
    if len(y) < target_len:
        y = np.pad(y, (0, target_len - len(y)))
    else:
        y = y[:target_len]

    features = []
    feature_names = []

    # MFCC
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
    mfcc_mean = np.mean(mfcc, axis=1)
    mfcc_std = np.std(mfcc, axis=1)
    features.extend(mfcc_mean)
    features.extend(mfcc_std)
    feature_names.extend([f"mfcc_mean_{i+1}" for i in range(N_MFCC)])
    feature_names.extend([f"mfcc_std_{i+1}" for i in range(N_MFCC)])

    # Delta MFCC
    delta_mfcc = librosa.feature.delta(mfcc)
    delta_mfcc_mean = np.mean(delta_mfcc, axis=1)
    features.extend(delta_mfcc_mean)
    feature_names.extend([f"delta_mfcc_mean_{i+1}" for i in range(N_MFCC)])

    # Mel Spectrogram
    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=N_MELS)
    mel_max = float(np.max(mel)) if mel.size > 0 else 0.0
    mel_ref = max(mel_max, 1e-6)
    mel_db = librosa.power_to_db(mel, ref=mel_ref)
    mel_mean = np.mean(mel_db, axis=1)
    mel_std = np.std(mel_db, axis=1)
    features.extend(mel_mean)
    features.extend(mel_std)
    feature_names.extend([f"mel_mean_{i+1}" for i in range(N_MELS)])
    feature_names.extend([f"mel_std_{i+1}" for i in range(N_MELS)])

    # Chroma
    try:
        if np.max(np.abs(y)) < 1e-4 or float(np.std(y)) < 1e-5:
            chroma = librosa.feature.chroma_stft(y=y, sr=sr, tuning=0.0)
        else:
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    except Exception:
        chroma = np.zeros((12, 1), dtype=np.float32)
    chroma_mean = np.mean(chroma, axis=1)
    features.extend(chroma_mean)
    feature_names.extend([f"chroma_mean_{i+1}" for i in range(12)])

    # Spectral Contrast
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    contrast_mean = np.mean(contrast, axis=1)
    features.extend(contrast_mean)
    feature_names.extend([f"contrast_mean_{i+1}" for i in range(len(contrast_mean))]) # typically 7

    # Zero Crossing Rate
    zcr = librosa.feature.zero_crossing_rate(y)
    features.append(np.mean(zcr))
    features.append(np.std(zcr))
    feature_names.extend(["zcr_mean", "zcr_std"])

    # RMS
    rms = librosa.feature.rms(y=y)
    features.append(np.mean(rms))
    features.append(np.std(rms))
    feature_names.extend(["rms_mean", "rms_std"])

    # Spectral Rolloff
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
    features.append(np.mean(rolloff))
    feature_names.append("rolloff_mean")

    feat_arr = np.nan_to_num(np.array(features, dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    return feat_arr, feature_names
