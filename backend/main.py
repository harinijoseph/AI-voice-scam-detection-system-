import os
import sys

# Ensure repository root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routes.health import router as health_router
from backend.routes.presets import router as presets_router
from backend.routes.analyze import router as analyze_router
from backend.routes.verification import router as verification_router
from backend.routes.benchmarks import router as benchmarks_router
from backend.config import DATA_DIR

app = FastAPI(
    title="VoxSentinel AI Defense Framework API",
    description="Multimodal Zero-Shot Voice Deepfake and Telephony Scam Detection System",
    version="2.0.0"
)

# Enable CORS for local Vite development (port 3000, 5173, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all modular routers
app.include_router(health_router)
app.include_router(presets_router)
app.include_router(analyze_router)
app.include_router(verification_router)
app.include_router(benchmarks_router)

# Mount audio data directory for direct static streaming if needed
os.makedirs(DATA_DIR, exist_ok=True)
app.mount("/audio_static", StaticFiles(directory=DATA_DIR), name="audio_static")

# Mount React production build if available
FRONTEND_DIST = os.path.join(PROJECT_ROOT, "frontend", "dist")
if os.path.exists(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {
            "framework": "VoxSentinel AI Defense System",
            "status": "online",
            "documentation": "/docs",
            "health": "/api/health"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

