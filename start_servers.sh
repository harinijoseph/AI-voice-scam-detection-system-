#!/bin/bash
# ==============================================================================
# VoxSentinel AI — Full-Stack Server Launch Script
# Starts FastAPI backend (port 8000) and serves the React application directly
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================================================="
echo "🛡️  VoxSentinel AI — Full-Stack Server Launcher"
echo "=========================================================================="

# Build frontend if needed
if [ ! -d "frontend/dist" ]; then
    echo "📦 Building React production bundle in frontend/dist..."
    cd frontend && npm install && npm run build && cd ..
fi

echo "🚀 Starting FastAPI Backend & React App on http://localhost:8000..."
echo "API Documentation available at: http://localhost:8000/docs"
echo "Live Web Dashboard at:          http://localhost:8000/"
echo "=========================================================================="

exec ./venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
