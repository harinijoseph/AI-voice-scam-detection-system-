import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
PHASE5_DIR = os.path.join(DATA_DIR, "phase5")
DATASET_DIR = os.path.join(PROJECT_ROOT, "human-nonhuman")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(PHASE5_DIR, exist_ok=True)
