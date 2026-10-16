import os
import random
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from src.utils.sample_generator import generate_demo_samples
from backend.config import DATA_DIR, DATASET_DIR

router = APIRouter(prefix="/api/presets", tags=["Presets"])

# Cache generated presets in memory
_CACHED_SAMPLES = None

def get_demo_samples():
    global _CACHED_SAMPLES
    if _CACHED_SAMPLES is None:
        _CACHED_SAMPLES = generate_demo_samples(output_dir=DATA_DIR)
    return _CACHED_SAMPLES

@router.get("")
def list_presets():
    samples = get_demo_samples()
    preset_list = []
    
    # Preset metadata mapping
    meta = {
        "Legitimate Family Call": {
            "id": "legitimate_family_call",
            "threat_level": "safe",
            "tag": "Authentic Voice",
            "description": "Natural human conversation with vocal intonation drift and zero financial coercion."
        },
        "AI Cloned Emergency Scam (Grandparent Trap)": {
            "id": "ai_grandparent_scam",
            "threat_level": "danger",
            "tag": "Urgent Family Trap",
            "description": "Zero-shot neural voice clone demanding immediate $5,000 cash bail under isolation pressure."
        },
        "AI Bank Impersonation & Credential Harvest": {
            "id": "ai_bank_fraud",
            "threat_level": "danger",
            "tag": "Credential Harvesting",
            "description": "Synthetic financial agent impersonation claiming account freeze and harvesting 6-digit OTP."
        },
        "Tech Support Remote Access Scam": {
            "id": "ai_tech_support",
            "threat_level": "danger",
            "tag": "Remote Access Extortion",
            "description": "Extortion scam coercing victim into installing AnyDesk malware to remediate fake virus infection."
        }
    }

    for name, data in samples.items():
        m = meta.get(name, {
            "id": name.lower().replace(" ", "_"),
            "threat_level": "unknown",
            "tag": "Preset Scenario",
            "description": ""
        })
        preset_list.append({
            "key": name,
            "id": m["id"],
            "name": name,
            "threat_level": m["threat_level"],
            "tag": m["tag"],
            "description": m["description"],
            "transcript": data.get("transcript", ""),
            "audio_url": f"/api/presets/{m['id']}/audio",
            "file_exists": os.path.exists(data.get("file", ""))
        })

    return {"presets": preset_list}


@router.get("/dataset-random")
def get_random_dataset_preset(category: str = Query("human", description="human or nonhuman")):
    """
    Returns a random sample from human-nonhuman/human or nonhuman for instant scanner testing.
    """
    cat = "human" if category == "human" else "nonhuman"
    cat_dir = os.path.join(DATASET_DIR, cat)
    if not os.path.exists(cat_dir):
        raise HTTPException(status_code=404, detail="Dataset directory not found")

    files = [f for f in os.listdir(cat_dir) if f.endswith(".mp3")]
    if not files:
        raise HTTPException(status_code=404, detail="No audio files found in dataset")

    chosen = random.choice(files)
    label = "Genuine Human Voice" if cat == "human" else "AI Voice Clone (Synthetic)"
    threat = "safe" if cat == "human" else "danger"

    return {
        "id": f"dataset_{cat}_{chosen[:8]}",
        "category": cat,
        "filename": chosen,
        "name": f"Dataset Sample: {label}",
        "threat_level": threat,
        "tag": f"human-nonhuman/{cat}",
        "description": f"Real empirical speech recording from dataset '{cat}' folder ({chosen[:20]}...).",
        "audio_url": f"/api/benchmarks/dataset/audio/{cat}/{chosen}",
        "transcript": ""
    }


@router.get("/{preset_id}/audio")
def stream_preset_audio(preset_id: str):
    samples = get_demo_samples()
    id_map = {
        "legitimate_family_call": "Legitimate Family Call",
        "ai_grandparent_scam": "AI Cloned Emergency Scam (Grandparent Trap)",
        "ai_bank_fraud": "AI Bank Impersonation & Credential Harvest",
        "ai_tech_support": "Tech Support Remote Access Scam"
    }

    key = id_map.get(preset_id)
    if not key or key not in samples:
        raise HTTPException(status_code=404, detail="Preset not found")

    file_path = samples[key].get("file")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Preset audio file missing on disk")

    return FileResponse(file_path, media_type="audio/wav", filename=f"{preset_id}.wav")
