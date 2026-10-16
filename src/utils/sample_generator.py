import os
import wave
import struct
import numpy as np

def generate_demo_samples(output_dir="data"):
    """Generates audio `.wav` files using Python built-in wave module for maximum compatibility."""
    os.makedirs(output_dir, exist_ok=True)

    sr = 22050
    duration = 4.0 # 4 seconds each
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    samples_info = {}

    def save_wav(filename, signal):
        filepath = os.path.join(output_dir, filename)
        with wave.open(filepath, 'w') as wf:
            wf.setnchannels(1) # mono
            wf.setsampwidth(2) # 16-bit
            wf.setframerate(sr)
            packed_data = struct.pack(f'<{len(signal)}h', *signal)
            wf.writeframes(packed_data)
        return filepath

    # Use genuine recorded audio clips if available in data/phase1/
    real_sample_src = os.path.join(output_dir, "phase1", "real", "real_clip_001.wav")
    fake_sample_1_src = os.path.join(output_dir, "phase1", "fake", "fake_clip_001.wav")
    fake_sample_2_src = os.path.join(output_dir, "phase1", "fake", "fake_clip_002.wav")
    fake_sample_3_src = os.path.join(output_dir, "phase1", "fake", "fake_clip_003.wav")

    import shutil

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    human_dir = os.path.join(project_root, "human-nonhuman", "human")
    nonhuman_dir = os.path.join(project_root, "human-nonhuman", "nonhuman")

    def _convert_or_copy(src_path, dest_path):
        try:
            import librosa
            import soundfile as sf
            y, _ = librosa.load(src_path, sr=16000)
            if len(y) > 16000 * 12: # Trim to 12s for demo presets if longer
                y = y[:16000 * 12]
            sf.write(dest_path, y, 16000, subtype='PCM_16')
            return True
        except Exception:
            return False

    # Check for human-nonhuman dataset first
    has_dataset = (
        os.path.exists(human_dir) and os.path.exists(nonhuman_dir) and
        len(os.listdir(human_dir)) > 0 and len(os.listdir(nonhuman_dir)) > 0
    )

    path_legit = os.path.join(output_dir, "sample_legitimate_call.wav")
    path_scam1 = os.path.join(output_dir, "sample_ai_grandparent_scam.wav")
    path_scam2 = os.path.join(output_dir, "sample_ai_bank_fraud.wav")
    path_scam3 = os.path.join(output_dir, "sample_ai_tech_support.wav")

    if has_dataset:
        h_files = sorted([f for f in os.listdir(human_dir) if f.endswith(".mp3") or f.endswith(".wav")])
        nh_files = sorted([f for f in os.listdir(nonhuman_dir) if f.endswith(".mp3") or f.endswith(".wav")])

        if h_files:
            _convert_or_copy(os.path.join(human_dir, h_files[1]), path_legit)
        if len(nh_files) >= 1:
            _convert_or_copy(os.path.join(nonhuman_dir, nh_files[0]), path_scam1)
        if len(nh_files) >= 2:
            _convert_or_copy(os.path.join(nonhuman_dir, nh_files[1]), path_scam2)
        if len(nh_files) >= 3:
            _convert_or_copy(os.path.join(nonhuman_dir, nh_files[2]), path_scam3)
    elif os.path.exists(real_sample_src):
        shutil.copyfile(real_sample_src, path_legit)
        if os.path.exists(fake_sample_1_src):
            shutil.copyfile(fake_sample_1_src, path_scam1)
        if os.path.exists(fake_sample_2_src):
            shutil.copyfile(fake_sample_2_src, path_scam2)
        if os.path.exists(fake_sample_3_src):
            shutil.copyfile(fake_sample_3_src, path_scam3)
    else:
        # Fallback synthesis
        f0_legit = 180 + 20 * np.sin(2 * np.pi * 1.5 * t) + 15 * np.sin(2 * np.pi * 4.2 * t)
        y_legit = 0.4 * np.sin(2 * np.pi * f0_legit * t) + 0.1 * np.random.normal(0, 0.05, len(t))
        y_legit[int(sr * 1.8):int(sr * 2.2)] *= 0.1
        y_legit_int = (y_legit / np.max(np.abs(y_legit)) * 32000).astype(np.int16)
        path_legit = save_wav("sample_legitimate_call.wav", y_legit_int)

        f0_synth = 240 + 2.0 * np.sin(2 * np.pi * 0.2 * t)
        y_scam1 = 0.5 * np.sin(2 * np.pi * f0_synth * t) + 0.25 * np.sin(2 * np.pi * f0_synth * 2 * t)
        y_scam1_int = (y_scam1 / np.max(np.abs(y_scam1)) * 32000).astype(np.int16)
        path_scam1 = save_wav("sample_ai_grandparent_scam.wav", y_scam1_int)

        f0_bank = 140 + 1.0 * np.sin(2 * np.pi * 0.1 * t)
        y_scam2 = 0.5 * np.sin(2 * np.pi * f0_bank * t) + 0.15 * np.sin(2 * np.pi * f0_bank * 3 * t)
        y_scam2_int = (y_scam2 / np.max(np.abs(y_scam2)) * 32000).astype(np.int16)
        path_scam2 = save_wav("sample_ai_bank_fraud.wav", y_scam2_int)

        f0_tech = 195 + 1.5 * np.sin(2 * np.pi * 0.3 * t)
        y_scam3 = 0.5 * np.sin(2 * np.pi * f0_tech * t) + 0.2 * np.sin(2 * np.pi * f0_tech * 2.5 * t)
        y_scam3_int = (y_scam3 / np.max(np.abs(y_scam3)) * 32000).astype(np.int16)
        path_scam3 = save_wav("sample_ai_tech_support.wav", y_scam3_int)

    samples_info["Legitimate Family Call"] = {
        "file": path_legit,
        "transcript": "Hey Mom, just wanted to check if we are still meeting for dinner on Saturday at 7 PM? Call me back when you get a chance!",
        "description": "Natural human voice with organic pitch drift, harmonic resonance, and respiratory pauses."
    }

    samples_info["AI Cloned Emergency Scam (Grandparent Trap)"] = {
        "file": path_scam1,
        "transcript": "Grandma please help me! It's your grandson. I got into a terrible car crash and I am held in jail right now. I need $5,000 wire transfer or Zelle payment immediately for bail! Please do not hang up or tell my parents!",
        "description": "Synthetic zero-shot neural voice clone combined with emergency impersonation and urgent financial extraction."
    }

    samples_info["AI Bank Impersonation & Credential Harvest"] = {
        "file": path_scam2,
        "transcript": "Hello this is Officer Miller from the Fraud Department. Your bank account has been compromised right now. Do not hang up or freeze your account immediately. Send your OTP verification code right now.",
        "description": "Synthesized institutional voice with artificial panic induction and one-time password (OTP) harvesting."
    }

    samples_info["Tech Support Remote Access Scam"] = {
        "file": path_scam3,
        "transcript": "Warning from Microsoft Security Support! Severe malware virus detected on your personal computer. Download AnyDesk or TeamViewer immediately and grant remote access to prevent hard drive destruction.",
        "description": "Synthetic automated voice prompt attempting unauthorized remote desktop takeover."
    }

    return samples_info
