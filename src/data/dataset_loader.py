import os
import soundfile as sf
import numpy as np
import io
import datasets
from datasets import load_dataset, Audio

def prepare_phase1_dataset(base_dir="data/phase1", num_clips_per_class=200, sr=22050, duration=3.0):
    """
    Downloads and prepares a real deepfake audio dataset from Hugging Face:
    koyyalamudiraghavendra/deepfake-audio-detection
    Extracts authentic and synthetic speech into .wav files.
    """
    real_dir = os.path.join(base_dir, "real")
    fake_dir = os.path.join(base_dir, "fake")
    os.makedirs(real_dir, exist_ok=True)
    os.makedirs(fake_dir, exist_ok=True)

    # Check if clips are already cached locally
    existing_reals = [os.path.join(real_dir, f) for f in sorted(os.listdir(real_dir)) if f.endswith(".wav")]
    existing_fakes = [os.path.join(fake_dir, f) for f in sorted(os.listdir(fake_dir)) if f.endswith(".wav")]
    if len(existing_reals) >= num_clips_per_class and len(existing_fakes) >= num_clips_per_class:
        return existing_reals[:num_clips_per_class], existing_fakes[:num_clips_per_class]

    print("Downloading Hugging Face deepfake dataset... (This may take a moment)")
    ds = load_dataset("koyyalamudiraghavendra/deepfake-audio-detection", split="train")
    
    # Cast column to prevent HF from trying to use torchcodec to decode
    ds = ds.cast_column("audio", Audio(decode=False))

    real_files = []
    fake_files = []

    real_count = 0
    fake_count = 0

    for item in ds:
        if real_count >= num_clips_per_class and fake_count >= num_clips_per_class:
            break

        label = item.get("label", "")
        audio_data = item.get("audio", {})
        
        if not audio_data or "bytes" not in audio_data:
            continue

        # Decode raw bytes using soundfile directly
        audio_bytes = audio_data["bytes"]
        audio_array, original_sr = sf.read(io.BytesIO(audio_bytes))

        # Truncate to duration to match original codebase speed requirements
        max_samples = int(original_sr * duration)
        if len(audio_array) > max_samples:
            audio_array = audio_array[:max_samples]

        if label == 0 and real_count < num_clips_per_class:
            filepath = os.path.join(real_dir, f"real_clip_{real_count+1:03d}.wav")
            sf.write(filepath, audio_array, original_sr)
            real_files.append(filepath)
            real_count += 1
            
        elif label == 1 and fake_count < num_clips_per_class:
            filepath = os.path.join(fake_dir, f"fake_clip_{fake_count+1:03d}.wav")
            sf.write(filepath, audio_array, original_sr)
            fake_files.append(filepath)
            fake_count += 1

    return real_files, fake_files

if __name__ == "__main__":
    reals, fakes = prepare_phase1_dataset()
    print(f"Dataset ready: {len(reals)} real clips, {len(fakes)} fake clips created in data/phase1/")
