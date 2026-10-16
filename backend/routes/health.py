from fastapi import APIRouter
import torch

router = APIRouter(prefix="/api/health", tags=["Health"])

@router.get("")
def health_check():
    has_mps = torch.backends.mps.is_available() if hasattr(torch.backends, "mps") else False
    has_cuda = torch.cuda.is_available()
    device = "cuda" if has_cuda else ("mps" if has_mps else "cpu")
    return {
        "status": "healthy",
        "service": "VoxSentinel AI Defense Backend",
        "version": "2.0.0",
        "device": device,
        "monitoring_active": True
    }
