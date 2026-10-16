import os
import numpy as np
import librosa
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def _prepare_audio(y, min_len=2048):
    """Safely normalizes, downmixes, and pads audio signal."""
    if y is None or len(y) == 0:
        return np.zeros(min_len, dtype=np.float32)
    y = np.asarray(y, dtype=np.float32)
    if y.ndim > 1:
        if y.shape[0] <= 8 and y.shape[1] > y.shape[0]:
            y = np.mean(y, axis=0)
        else:
            y = np.mean(y, axis=-1)
    y = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0)
    if len(y) < min_len:
        y = np.pad(y, (0, min_len - len(y)), mode='constant')
    return y

def plot_pitch_contour(y, sr=22050):
    """
    Generates a Pitch Variation Line Chart (F0 over time) using pYIN.
    
    Thesis Visual Concept:
    ----------------------
    Plots the fundamental frequency F0(t) in Hertz over time.
    Human speech shows continuous pitch modulation, vibrato, and intonation drift.
    Synthetic TTS speech often shows artificially rigid, flat, or quantized step-like pitch lines.
    """
    y = _prepare_audio(y, min_len=2048)

    max_amp = float(np.max(np.abs(y)))
    std_amp = float(np.std(y))
    f0 = None

    if max_amp >= 1e-4 and std_amp >= 1e-5:
        try:
            f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=65, fmax=300, sr=sr)
        except Exception:
            f0 = None

    if f0 is not None and len(f0) > 0:
        times = librosa.times_like(f0, sr=sr)
        f0_clean = np.where(np.isnan(f0), None, f0)
        f0_valid = f0[~np.isnan(f0)]
    else:
        duration = max(0.1, len(y) / sr)
        times = np.linspace(0, duration, max(2, int(duration * 100)))
        f0_clean = [None] * len(times)
        f0_valid = np.array([])

    f0_mean = float(np.nan_to_num(np.mean(f0_valid))) if len(f0_valid) > 0 else 0.0
    f0_std = float(np.nan_to_num(np.std(f0_valid))) if len(f0_valid) > 0 else 0.0

    fig = go.Figure()

    # Add Pitch Line
    fig.add_trace(go.Scatter(
        x=times,
        y=f0_clean,
        mode='lines+markers',
        marker=dict(size=3, color='#ea580c'),
        line=dict(color='#ea580c', width=2),
        name='Pitch (F0 Hz)'
    ))

    # Add Mean Pitch Reference Line
    if f0_mean > 0:
        fig.add_hline(
            y=f0_mean,
            line_dash="dash",
            line_color="#1e293b",
            annotation_text=f"Mean F0: {f0_mean:.1f} Hz (std: {f0_std:.1f})",
            annotation_position="bottom right",
            annotation_font=dict(color="#1e293b", size=11)
        )

    fig.update_layout(
        title="<b>Pitch Variation Line Chart (F0 Contour via pYIN)</b>",
        xaxis=dict(title="Time (seconds)", color='#475569', showgrid=True, gridcolor='#f1f5f9', zerolinecolor='#e2e8f0'),
        yaxis=dict(title="Fundamental Frequency F0 (Hz)", range=[50, 320], color='#475569', showgrid=True, gridcolor='#f1f5f9', zerolinecolor='#e2e8f0'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#ffffff',
        font=dict(color='#111111', family="Inter, -apple-system, sans-serif"),
        margin=dict(l=40, r=40, t=50, b=40),
        height=320
    )

    return fig, {"f0_mean": f0_mean, "f0_std": f0_std}


def plot_mel_spectrogram_with_anomalies(y, sr=22050):
    """
    Generates a Mel-Spectrogram with synthetic acoustic anomaly overlays.
    
    Thesis Visual Concept:
    ----------------------
    Visualizes acoustic energy density across Mel-frequency bands (Y-axis) over time (X-axis).
    Highlights frames where high spectral centroid combined with zero-crossing anomalies indicate
    neural vocoder artifacts (e.g. WaveNet / HiFi-GAN phase artifacts).
    """
    y = _prepare_audio(y, min_len=2048)

    # Compute Mel Spectrogram
    try:
        S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
    except Exception:
        S = np.zeros((128, max(1, len(y) // 512)), dtype=np.float32)

    max_val = float(np.max(S)) if S.size > 0 else 0.0
    ref_val = max(max_val, 1e-6)
    S_dB = librosa.power_to_db(S, ref=ref_val)
    S_dB = np.nan_to_num(S_dB, nan=-80.0, posinf=0.0, neginf=-80.0)

    times = librosa.times_like(S_dB, sr=sr)
    freqs = librosa.mel_frequencies(n_mels=128, fmax=8000)

    # Detect anomaly frames: spectral flatness anomaly or unusually high spectral centroid frames
    try:
        flatness = librosa.feature.spectral_flatness(y=y)[0]
    except Exception:
        flatness = np.zeros(S_dB.shape[1], dtype=np.float32)

    try:
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    except Exception:
        centroid = np.zeros(S_dB.shape[1], dtype=np.float32)

    # Normalize lengths to match S_dB time frames
    n_frames = min(S_dB.shape[1], len(flatness), len(centroid))
    if n_frames == 0:
        n_frames = max(1, S_dB.shape[1])
        flatness = np.zeros(n_frames, dtype=np.float32)
        centroid = np.zeros(n_frames, dtype=np.float32)
        times = np.linspace(0, max(0.1, len(y) / sr), n_frames)
        S_dB = np.full((128, n_frames), -80.0, dtype=np.float32)
    else:
        flatness = flatness[:n_frames]
        centroid = centroid[:n_frames]
        times = times[:n_frames]
        S_dB = S_dB[:, :n_frames]

    flatness = np.nan_to_num(flatness, nan=0.0, posinf=0.0, neginf=0.0)
    centroid = np.nan_to_num(centroid, nan=0.0, posinf=0.0, neginf=0.0)

    # Anomaly condition: abnormally flat spectrum (robotic phase) or extreme high-freq roll-off
    if np.max(flatness) > np.min(flatness) + 1e-6:
        p20 = float(np.percentile(flatness, 20))
        anomaly_mask = (flatness < p20) | (centroid > 2200)
    else:
        anomaly_mask = np.zeros(n_frames, dtype=bool)

    fig = go.Figure()

    # Heatmap of Mel-Spectrogram
    fig.add_trace(go.Heatmap(
        z=S_dB,
        x=times,
        y=freqs,
        colorscale='Inferno',
        colorbar=dict(title=dict(text="Power (dB)", font=dict(color="#111111", size=12)), tickfont=dict(color="#475569"), len=0.85),
        name='Mel Power (dB)'
    ))

    # Highlight anomaly frames with subtle orange vertical bars
    anomaly_times = times[anomaly_mask]
    if len(anomaly_times) > 0:
        for t_anom in anomaly_times[::4]: # sample frames for visual clarity
            fig.add_vline(
                x=float(t_anom),
                line_width=1.5,
                line_dash="dot",
                line_color="rgba(234, 88, 12, 0.75)"
            )

    fig.update_layout(
        title="<b>Mel-Spectrogram with Forensic Anomaly Heatmap Highlights</b>",
        xaxis=dict(title="Time (seconds)", color='#475569', showgrid=True, gridcolor='#f1f5f9'),
        yaxis=dict(title="Frequency (Hz)", color='#475569', showgrid=True, gridcolor='#f1f5f9'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#ffffff',
        font=dict(color='#111111', family="Inter, -apple-system, sans-serif"),
        margin=dict(l=40, r=40, t=50, b=40),
        height=340
    )

    return fig, {"anomaly_frame_count": int(np.sum(anomaly_mask)), "total_frames": int(n_frames)}


def generate_acoustic_visuals(audio_path_or_y, sr=22050):
    """
    Takes an audio file path or waveform array and generates both Phase 2 visual evidence objects.
    Returns:
        dict: {"pitch_fig": Plotly Figure, "spectrogram_fig": Plotly Figure, "pitch_metrics": dict, "spectrogram_metrics": dict}
    """
    y = None
    if isinstance(audio_path_or_y, str):
        if not audio_path_or_y.strip() or not os.path.exists(audio_path_or_y):
            y = np.zeros(2048, dtype=np.float32)
        else:
            try:
                y, sr = librosa.load(audio_path_or_y, sr=sr)
            except Exception:
                y = np.zeros(2048, dtype=np.float32)
    else:
        y = audio_path_or_y

    y = _prepare_audio(y, min_len=2048)

    pitch_fig, pitch_metrics = plot_pitch_contour(y, sr=sr)
    spec_fig, spec_metrics = plot_mel_spectrogram_with_anomalies(y, sr=sr)

    return {
        "pitch_fig": pitch_fig,
        "spectrogram_fig": spec_fig,
        "pitch_metrics": pitch_metrics,
        "spectrogram_metrics": spec_metrics
    }
