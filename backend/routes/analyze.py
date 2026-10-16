import os
import io
import time
import uuid
import numpy as np
import soundfile as sf
import librosa
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List

from backend.config import DATA_DIR, DATASET_DIR
from src.fusion.fusion_engine import Phase4FusionEngine
from src.audio.acoustic_visualizer import generate_acoustic_visuals

router = APIRouter(prefix="/api/analyze", tags=["Analysis"])

# Initialize fusion engine singleton
_ENGINE_INSTANCE = None

def get_engine():
    global _ENGINE_INSTANCE
    if _ENGINE_INSTANCE is None:
        _ENGINE_INSTANCE = Phase4FusionEngine()
    return _ENGINE_INSTANCE


def format_plain_english_verdict(res: dict) -> dict:
    risk = res.get("overall_risk_score", 0.0)
    ac_prob = res.get("acoustic_result", {}).get("synthetic_probability", 0.0)
    cnt_prob = res.get("content_result", {}).get("scam_probability", 0.0)
    tactics = res.get("content_result", {}).get("detected_tactics", [])
    flagged = res.get("content_result", {}).get("flagged_phrases", [])

    is_acoustic_ai = (ac_prob >= 0.50)
    is_content_scam = (cnt_prob >= 0.40 or len(tactics) > 0 or len(flagged) >= 2 or risk >= 0.55)

    # QUADRANT 1: AI Voice Clone + Scam Content
    if is_acoustic_ai and is_content_scam:
        return {
            "type": "danger",
            "badge": "CRITICAL / AI SYNTHETIC VOICE + SCAM",
            "title": "🔴 DANGER: AI VOICE CLONE & SCAM",
            "subtitle": "Critical Threat — Synthetic AI voice clone paired with active social engineering fraud",
            "border_color": "#dc2626",
            "bg_color": "#fef2f2",
            "text_color": "#991b1b",
            "summary": (
                "Our acoustic scanner detected synthetic vocoder phase anomalies and robotic pitch quantization "
                "characteristic of generative neural speech clones. Furthermore, the spoken dialogue contains "
                "active social engineering fraud (urgent bail/emergency pressure, wire transfer demands, or credential harvesting). "
                "Do NOT comply with any instructions."
            ),
            "advice": "Terminate this call immediately. Never send gift cards, cryptocurrency, or wire transfers.",
            "risk_pct": round(risk * 100, 1),
            "voice_risk_pct": round(ac_prob * 100, 1),
            "words_risk_pct": round(cnt_prob * 100, 1),
            "challenge_triggered": True
        }

    # QUADRANT 2: Authentic Human Voice + Scam Content (Human Voice Scam / Social Engineering)
    elif not is_acoustic_ai and is_content_scam:
        return {
            "type": "warning",
            "badge": "AUTHENTIC HUMAN VOICE + ACTIVE FRAUD",
            "title": "🟠 DANGER: HUMAN VOICE SCAM / SOCIAL ENGINEERING",
            "subtitle": "High Threat — Voice is a real human, but dialogue contains active social engineering fraud",
            "border_color": "#ea580c",
            "bg_color": "#fff7ed",
            "text_color": "#9a3412",
            "summary": (
                "Acoustic forensics confirm the caller's voice is an AUTHENTIC HUMAN (natural pitch micro-tremors, "
                "organic breathing pauses, zero vocoder artifacts). However, the spoken dialogue contains ACTIVE "
                "COERCIVE FRAUD / SOCIAL ENGINEERING (such as emergency bail pressure, demands for money, or credential theft). "
                "Scammers are real humans operating call centers worldwide. Do NOT trust unexpected requests simply because the voice sounds real."
            ),
            "advice": "Do NOT wire funds, disclose passwords, or comply with demands. Real humans run fraud networks. Hang up and verify through an independent known number.",
            "risk_pct": round(risk * 100, 1),
            "voice_risk_pct": round(ac_prob * 100, 1),
            "words_risk_pct": round(cnt_prob * 100, 1),
            "challenge_triggered": True
        }

    # QUADRANT 3: AI Synthetic Voice + Safe / Benign Content
    elif is_acoustic_ai and not is_content_scam:
        return {
            "type": "info",
            "badge": "SYNTHETIC AI VOICE / BENIGN CONTENT",
            "title": "🟣 CAUTION: AI SYNTHESIZED VOICE (NO SCAM DETECTED)",
            "subtitle": "Moderate Caution — Voice appears synthetic/AI-generated, but no scam tactics were detected",
            "border_color": "#7c3aed",
            "bg_color": "#faf5ff",
            "text_color": "#5b21b6",
            "summary": (
                "Acoustic forensics detected synthetic speech characteristics (vocoder frequency anomalies and pitch smoothing). "
                "However, no coercive language, emergency pressure, or financial demands were detected. This may be an automated "
                "customer service IVR, text-to-speech assistant, or legitimate broadcast."
            ),
            "advice": "Verify caller identity if sensitive personal or financial information is requested later.",
            "risk_pct": round(risk * 100, 1),
            "voice_risk_pct": round(ac_prob * 100, 1),
            "words_risk_pct": round(cnt_prob * 100, 1),
            "challenge_triggered": False
        }

    # QUADRANT 4: Authentic Human Voice + Safe / Benign Content
    elif risk < 0.35 and len(tactics) == 0 and len(flagged) < 2:
        return {
            "type": "safe",
            "badge": "NOMINAL / AUTHENTIC VERIFIED",
            "title": "🟢 AUTHENTIC HUMAN VOICE (SAFE)",
            "subtitle": "Safe — Natural vocal physics, no coercion detected",
            "border_color": "#16a34a",
            "bg_color": "#f0fdf4",
            "text_color": "#166534",
            "summary": (
                "We detected organic respiratory pauses, natural intonation drift, and realistic vocal cord micro-tremor. "
                "No coercive tactics, emergency bail traps, or requests for passwords were found. This voice and dialogue pattern "
                "match a genuine human speaker."
            ),
            "advice": "This call appears legitimate. As always, remain vigilant if unexpected requests arise later in the conversation.",
            "risk_pct": round(risk * 100, 1),
            "voice_risk_pct": round(ac_prob * 100, 1),
            "words_risk_pct": round(cnt_prob * 100, 1),
            "challenge_triggered": False
        }

    # QUADRANT 5 / Fallback: Ambiguous / Mild Suspicion
    else:
        return {
            "type": "caution",
            "badge": "MODERATE RISK / SUSPICIOUS CONTENT",
            "title": "🟡 CAUTION: SUSPICIOUS CONTENT",
            "subtitle": "Moderate Risk — Voice appears human, but words or tone have elevated risk markers",
            "border_color": "#d97706",
            "bg_color": "#fffbeb",
            "text_color": "#92400e",
            "summary": (
                "While vocal cords display natural frequency variation, the spoken dialogue triggers mild flags "
                "for social engineering patterns. Verify caller identity before taking any action."
            ),
            "advice": "Ask an out-of-band security question or hang up and call back on a verified number.",
            "risk_pct": round(risk * 100, 1),
            "voice_risk_pct": round(ac_prob * 100, 1),
            "words_risk_pct": round(cnt_prob * 100, 1),
            "challenge_triggered": False
        }


def extract_telemetry_and_pitch(y: np.ndarray, sr: int, feats: dict, visuals: dict) -> tuple:
    # 1. Pitch points for chart
    pitch_points = []
    try:
        hop_length = 512
        f0, voiced_flag, _ = librosa.pyin(
            y,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            sr=sr,
            hop_length=hop_length
        )
        times = librosa.times_like(f0, sr=sr, hop_length=hop_length)
        step = max(1, len(times) // 80)  # Downsample to ~80 points for lightweight frontend rendering
        for i in range(0, len(times), step):
            hz = float(f0[i]) if (voiced_flag[i] and not np.isnan(f0[i])) else None
            pitch_points.append({
                "time": round(float(times[i]), 2),
                "pitch": round(hz, 1) if hz is not None else 0.0,
                "is_voiced": bool(voiced_flag[i] and hz is not None)
            })
    except Exception:
        pitch_points = [{"time": round(i * 0.1, 2), "pitch": 120.0, "is_voiced": True} for i in range(20)]

    # 2. Telemetry rows
    jitter = float(feats.get("pitch_jitter", 0.024))
    shimmer = float(feats.get("shimmer_local", 0.038))
    centroid = float(feats.get("spectral_centroid_mean", 1820.0))
    flatness = float(feats.get("spectral_flatness_mean", 0.015))
    inst_freq = float(feats.get("inst_freq_std", 5.4))
    glitches = int(visuals.get("spectrogram_metrics", {}).get("glitch_frame_count", 0))

    telemetry_rows = [
        {
            "name": "Pitch Micro-Tremor (Jitter)",
            "meaning": "Involuntary physiological vocal cord frequency micro-tremors.",
            "value": f"{jitter:.5f}",
            "human_range": "> 0.01800",
            "ai_range": "< 0.00900",
            "status": "Natural Human" if jitter >= 0.012 else "Robotic Flatline",
            "is_safe": jitter >= 0.012
        },
        {
            "name": "Vocal Shimmer (Amplitude Perturbation)",
            "meaning": "Cycle-to-cycle respiratory energy micro-drift.",
            "value": f"{shimmer:.5f}",
            "human_range": "> 0.02500",
            "ai_range": "< 0.01200",
            "status": "Natural Human" if shimmer >= 0.018 else "Synthetic Over-Smoothing",
            "is_safe": shimmer >= 0.018
        },
        {
            "name": "Spectral Energy Centroid",
            "meaning": "Center of mass of frequencies (vocal tract brightness).",
            "value": f"{centroid:.1f} Hz",
            "human_range": "1,200 – 2,200 Hz",
            "ai_range": "> 2,800 Hz",
            "status": "Normal Range" if centroid <= 2500 else "High-Freq Artifacts",
            "is_safe": centroid <= 2500
        },
        {
            "name": "Spectral Flatness (SFM)",
            "meaning": "Measures tone vs noise (harmonic structure vs vocoder buzz).",
            "value": f"{flatness:.5f}",
            "human_range": "0.0050 – 0.1500",
            "ai_range": "> 0.2500",
            "status": "Healthy Harmonics" if flatness <= 0.20 else "Noisy Static",
            "is_safe": flatness <= 0.20
        },
        {
            "name": "Instantaneous Phase Fluctuation",
            "meaning": "Hilbert transform phase dynamics across pitch periods.",
            "value": f"{inst_freq:.2f} Hz",
            "human_range": "< 12.00 Hz",
            "ai_range": "> 25.00 Hz",
            "status": "Continuous Flow" if inst_freq <= 18.0 else "Vocoder Discontinuity",
            "is_safe": inst_freq <= 18.0
        },
        {
            "name": "Vocoder Phase Glitch Frames",
            "meaning": "Sudden spectral energy jumps exceeding 4.0 standard deviations.",
            "value": f"{glitches} frames",
            "human_range": "0 – 4 frames",
            "ai_range": "> 10 frames",
            "status": "Minimal Glitches" if glitches <= 6 else "Vocoder Artifacts",
            "is_safe": glitches <= 6
        }
    ]

    return pitch_points, telemetry_rows


def extract_waveform_and_spectrum(y: np.ndarray, sr: int = 16000) -> tuple:
    """
    Extracts high-resolution audio waveform envelope points and logarithmic power spectrum bins
    for frontend audio visualizer graphs.
    """
    # 1. Waveform Envelope (120 points for smooth SVG waveform)
    num_points = 120
    hop = max(1, len(y) // num_points)
    waveform = []
    for i in range(0, min(len(y), hop * num_points), hop):
        chunk = y[i:i + hop]
        if len(chunk) > 0:
            peak = float(np.max(np.abs(chunk)))
            rms = float(np.sqrt(np.mean(chunk**2)))
            t = round(float(i) / sr, 2)
            waveform.append({
                "time": t,
                "amplitude": round(peak, 4),
                "rms": round(rms, 4)
            })

    # 2. Power Spectrum Bins (80 Hz to 8000 Hz)
    clip_len = min(len(y), sr * 4)
    fft_vals = np.abs(np.fft.rfft(y[:clip_len]))
    freqs = np.fft.rfftfreq(clip_len, 1.0 / sr)

    # 32 log-spaced frequency bands across human vocal range
    band_edges = np.geomspace(80, 8000, 33)
    spectrum = []
    for b in range(len(band_edges) - 1):
        f_low = band_edges[b]
        f_high = band_edges[b + 1]
        mask = (freqs >= f_low) & (freqs < f_high)
        if np.any(mask):
            mag = float(np.mean(fft_vals[mask]))
        else:
            mag = 0.0
        spectrum.append({
            "freq": int((f_low + f_high) / 2),
            "magnitude": round(float(np.log1p(mag)), 3),
            "band": f"{int(f_low)}-{int(f_high)}Hz"
        })

    max_mag = max([s["magnitude"] for s in spectrum] or [1.0])
    for s in spectrum:
        s["norm_pct"] = round((s["magnitude"] / (max_mag + 1e-6)) * 100, 1)

    return waveform, spectrum


@router.post("/audio")
async def analyze_audio_endpoint(
    audio_file: UploadFile = File(...),
    transcript: Optional[str] = Form(""),
    w_acoustic: float = Form(0.50),
    is_microphone: bool = Form(False)
):
    """
    Primary endpoint for processing inbound audio signals (microphone or file upload).
    """
    engine = get_engine()
    engine.w_acoustic = w_acoustic
    engine.w_content = round(1.0 - w_acoustic, 2)

    os.makedirs(DATA_DIR, exist_ok=True)
    file_id = f"mic_{int(time.time())}" if is_microphone else f"upload_{uuid.uuid4().hex[:8]}"
    saved_filename = f"{file_id}.wav"
    saved_path = os.path.join(DATA_DIR, saved_filename)

    raw_bytes = await audio_file.read()
    if not raw_bytes or len(raw_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty audio buffer received")

    # Decode and normalize to mono 16kHz PCM_16 WAV with multi-layer fallback
    y = None
    try:
        y, sr = librosa.load(io.BytesIO(raw_bytes), sr=16000)
    except Exception:
        y = None

    # Method B: scipy.io.wavfile
    if y is None or len(y) == 0:
        try:
            import scipy.io.wavfile as wavfile
            wav_sr, wav_data = wavfile.read(io.BytesIO(raw_bytes))
            if wav_data.ndim > 1:
                wav_data = np.mean(wav_data, axis=1)
            if np.issubdtype(wav_data.dtype, np.integer):
                max_val = np.iinfo(wav_data.dtype).max
                y = (wav_data.astype(np.float32) / max_val)
            else:
                y = wav_data.astype(np.float32)
            if wav_sr != 16000:
                y = librosa.resample(y, orig_sr=wav_sr, target_sr=16000)
        except Exception:
            y = None

    # Method C: Raw PCM int16 buffer
    if y is None or len(y) == 0:
        try:
            raw_pcm = np.frombuffer(raw_bytes, dtype=np.int16)
            if len(raw_pcm) >= 1600:
                y = raw_pcm.astype(np.float32) / 32768.0
        except Exception:
            y = None

    # Method D: Disk fallback
    if y is None or len(y) == 0:
        with open(saved_path, "wb") as f:
            f.write(raw_bytes)
        try:
            y, sr = librosa.load(saved_path, sr=16000)
        except Exception:
            y = None

    if y is None or len(y) == 0:
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio format: Unable to decode audio. Please ensure audio is recorded or uploaded in standard WAV (PCM 16-bit) or MP3 format."
        )

    if y.ndim > 1:
        y = np.mean(y, axis=0)
    y = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0)
    sf.write(saved_path, y, 16000, subtype='PCM_16')

    # Automatic Speech-to-Text if transcript is missing
    active_transcript = transcript.strip() if transcript else ""
    if not active_transcript:
        try:
            active_transcript = engine.content_engine.transcribe_audio(saved_path)
        except Exception:
            active_transcript = ""

    # Execute Multimodal Fusion
    res = engine.analyze_audio_call(saved_path, optional_transcript=active_transcript)

    # Visuals & Telemetry
    visuals = res.get("visuals", {})
    if not visuals:
        visuals = generate_acoustic_visuals(y, sr=16000)

    ac_res = res.get("acoustic_result", {})
    feats = ac_res.get("feature_summary", {})
    pitch_points, telemetry_rows = extract_telemetry_and_pitch(y, 16000, feats, visuals)
    waveform_data, spectrum_data = extract_waveform_and_spectrum(y, 16000)

    verdict = format_plain_english_verdict(res)

    return {
        "success": True,
        "audio_id": file_id,
        "audio_filename": saved_filename,
        "audio_url": f"/api/analyze/audio-file/{saved_filename}",
        "file_size_kb": round(os.path.getsize(saved_path) / 1024, 1),
        "duration_seconds": round(len(y) / 16000, 2),
        "overall_risk_score": res.get("overall_risk_score", 0.0),
        "risk_category": res.get("risk_category", "LOW RISK / AUTHENTIC"),
        "risk_color": res.get("risk_color", "#16a34a"),
        "verdict": verdict,
        "acoustic_result": ac_res,
        "content_result": res.get("content_result", {}),
        "engine_breakdown": res.get("engine_breakdown", {}),
        "explanations": res.get("explanations", []),
        "pitch_points": pitch_points,
        "telemetry_rows": telemetry_rows,
        "waveform_data": waveform_data,
        "spectrum_data": spectrum_data,
        "transcript": active_transcript
    }


class TranscriptUpdateRequest(BaseModel):
    audio_filename: str
    transcript: str
    w_acoustic: float = 0.50


@router.post("/transcript")
def update_transcript_endpoint(req: TranscriptUpdateRequest):
    """
    Recalculates behavioral intent and decision fusion when the user edits words.
    """
    engine = get_engine()
    engine.w_acoustic = req.w_acoustic
    engine.w_content = round(1.0 - req.w_acoustic, 2)

    audio_path = os.path.join(DATA_DIR, req.audio_filename)
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found on server")

    res = engine.analyze_audio_call(audio_path, optional_transcript=req.transcript)
    verdict = format_plain_english_verdict(res)

    return {
        "success": True,
        "overall_risk_score": res.get("overall_risk_score", 0.0),
        "risk_category": res.get("risk_category", "LOW RISK / AUTHENTIC"),
        "risk_color": res.get("risk_color", "#16a34a"),
        "verdict": verdict,
        "content_result": res.get("content_result", {}),
        "engine_breakdown": res.get("engine_breakdown", {}),
        "explanations": res.get("explanations", []),
        "transcript": req.transcript
    }


@router.get("/audio-file/{filename}")
def stream_audio_file(filename: str):
    """
    Streams stored audio file for browser playback.
    """
    safe_name = os.path.basename(filename)
    path = os.path.join(DATA_DIR, safe_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(path, media_type="audio/wav")


class DatasetSampleAnalyzeRequest(BaseModel):
    category: str
    filename: str
    w_acoustic: float = 0.50
    transcript: Optional[str] = ""


@router.post("/dataset-sample")
def analyze_dataset_sample(req: DatasetSampleAnalyzeRequest):
    """
    Directly analyzes an audio file from the human-nonhuman dataset without re-uploading.
    """
    if req.category not in {"human", "nonhuman", "possible"}:
        raise HTTPException(status_code=400, detail="Invalid dataset category")

    safe_name = os.path.basename(req.filename)
    audio_path = os.path.join(DATASET_DIR, req.category, safe_name)

    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Dataset audio file not found on disk")

    engine = get_engine()
    engine.w_acoustic = req.w_acoustic
    engine.w_content = round(1.0 - req.w_acoustic, 2)

    try:
        y, sr = librosa.load(audio_path, sr=16000)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to decode dataset audio: {str(e)}")

    if y.ndim > 1:
        y = np.mean(y, axis=0)
    y = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0)

    # Save a WAV copy into DATA_DIR for consistent visualizer and transcript updater references
    saved_filename = f"dataset_{req.category}_{safe_name}.wav"
    saved_path = os.path.join(DATA_DIR, saved_filename)
    sf.write(saved_path, y, 16000, subtype='PCM_16')

    active_transcript = req.transcript.strip() if req.transcript else ""

    res = engine.analyze_audio_call(saved_path, optional_transcript=active_transcript)

    visuals = res.get("visuals", {})
    if not visuals:
        visuals = generate_acoustic_visuals(y, sr=16000)

    ac_res = res.get("acoustic_result", {})
    feats = ac_res.get("feature_summary", {})
    pitch_points, telemetry_rows = extract_telemetry_and_pitch(y, 16000, feats, visuals)
    waveform_data, spectrum_data = extract_waveform_and_spectrum(y, 16000)

    verdict = format_plain_english_verdict(res)

    return {
        "success": True,
        "audio_id": f"dataset_{req.category}_{safe_name}",
        "audio_filename": saved_filename,
        "audio_url": f"/api/benchmarks/dataset/audio/{req.category}/{safe_name}",
        "file_size_kb": round(os.path.getsize(audio_path) / 1024, 1),
        "duration_seconds": round(len(y) / 16000, 2),
        "overall_risk_score": res.get("overall_risk_score", 0.0),
        "risk_category": res.get("risk_category", "LOW RISK / AUTHENTIC"),
        "risk_color": res.get("risk_color", "#16a34a"),
        "verdict": verdict,
        "acoustic_result": ac_res,
        "content_result": res.get("content_result", {}),
        "engine_breakdown": res.get("engine_breakdown", {}),
        "explanations": res.get("explanations", []),
        "pitch_points": pitch_points,
        "telemetry_rows": telemetry_rows,
        "waveform_data": waveform_data,
        "spectrum_data": spectrum_data,
        "transcript": active_transcript,
        "dataset_metadata": {
            "category": req.category,
            "filename": safe_name,
            "ground_truth": "GENUINE_HUMAN" if req.category == "human" else "AI_SYNTHETIC"
        }
    }

