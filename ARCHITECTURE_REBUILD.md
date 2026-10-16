# VoxSentinel AI — Full-Stack Architecture Rebuild Report

**Date:** October 6, 2026  
**Framework:** React 19 (Frontend) + FastAPI / Uvicorn (Backend)  
**Live Endpoint:** `http://localhost:8000/`  
**API Docs:** `http://localhost:8000/docs`  
**Test Suite:** 53 / 53 Tests PASSED (100% GREEN)  

---

## 1. Architectural Overhaul Overview

The application architecture has been restructured from a monolithic Streamlit script into a modern, decoupled **Full-Stack Architecture**:

```
                               ┌───────────────────────────────────────────────┐
                               │           REACT 19 FRONTEND (Vite)            │
                               │   - Off-White Minimalist Canvas (#f8f9fa)     │
                               │   - Dark Slate Visual Cards (#0f172a)         │
                               │   - Matte Safety Orange Accents (#ea580c)     │
                               │   - Web Audio API Live Canvas Oscilloscope    │
                               │   - Interactive SVG Pitch Contour Chart       │
                               │   - 5 Dedicated Human-Understood Hubs         │
                               └──────────────────────┬────────────────────────┘
                                                      │ HTTP / REST / Multipart
                                                      ▼
                               ┌───────────────────────────────────────────────┐
                               │             FASTAPI ASYNC BACKEND             │
                               │   - Uvicorn ASGI Server (Port 8000)           │
                               │   - CORS Middleware                           │
                               │   - Static Production Asset Serving           │
                               │   - Dual Ingestion: WebM Blob & PCM WAV       │
                               └──────────────────────┬────────────────────────┘
                                                      │
             ┌─────────────────────────┬──────────────┴───────────┬─────────────────────────┐
             ▼                         ▼                          ▼                         ▼
   ┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
   │ Acoustic Engine   │     │ Semantic NLP      │     │ Decision Fusion   │     │ Active OPSEC      │
   │ - 400D Conformer  │     │ - Speech-to-Text  │     │ - Risk Meter      │     │ - Codeword Tool   │
   │ - pYIN Pitch Track│     │ - Funnel Stage    │     │ - Plain Verdict   │     │ - Cognitive Honey │
   │ - Shimmer / Jitter│     │ - Coercive Regex  │     │ - Telemetry Table │     │ - Memory Library  │
   └───────────────────┘     └───────────────────┘     └───────────────────┘     └───────────────────┘
```

---

## 2. Backend Architecture & Route Directory Structure

The backend is modularized under [`backend/`](file:///Users/harinijoseph/Desktop/ai%20scam/backend):

```
backend/
├── __init__.py
├── config.py                   # Global filesystem paths (data, models, benchmarks)
├── main.py                     # FastAPI entry point, CORS, routers, static mount
└── routes/
    ├── __init__.py
    ├── health.py               # GET  /api/health
    ├── presets.py              # GET  /api/presets
    │                           # GET  /api/presets/{preset_id}/audio
    ├── analyze.py              # POST /api/analyze/audio (mic or upload)
    │                           # POST /api/analyze/transcript (re-scoring)
    │                           # GET  /api/analyze/audio-file/{filename}
    ├── verification.py         # POST /api/verify/codeword
    │                           # GET  /api/verify/questions
    └── benchmarks.py           # GET  /api/benchmarks/matrix
                                # POST /api/benchmarks/run
```

### Complete API Route Reference

| Method | Endpoint | Description | Request Payload | Response Schema |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Service health & device check | None | `{"status": "healthy", "device": "mps", "monitoring_active": true}` |
| `GET` | `/api/presets` | List 4 threat scenarios | None | `{"presets": [ { "id", "name", "threat_level", "audio_url" } ]}` |
| `GET` | `/api/presets/{id}/audio` | Stream scenario audio | None | `audio/wav` binary stream |
| `POST` | `/api/analyze/audio` | Multimodal voice & intent scan | `multipart/form-data`: `audio_file`, `transcript`, `w_acoustic` | Full JSON analysis (verdict, risk score, telemetry, pitch points) |
| `POST` | `/api/analyze/transcript` | Real-time text intent update | `{"audio_filename", "transcript", "w_acoustic"}` | Updated risk score, detected tactics, and 4-stage funnel |
| `POST` | `/api/verify/codeword` | Out-of-Band secret challenge | `{"secret_codeword", "caller_response"}` | `{"verified": true/false, "status", "title", "action"}` |
| `GET` | `/api/verify/questions` | Episodic memory challenge prompts | None | `{"questions": [ { "id", "category", "question" } ]}` |
| `GET` | `/api/benchmarks/matrix` | Telephony degradation matrix | None | `{"matrix": [ ... ], "report_markdown": "..."}` |
| `POST` | `/api/benchmarks/run` | Execute Phase 5 live tests | None | `{"success": true, "report_markdown": "..."}` |

---

## 3. React Frontend Architecture

The frontend is built with **React 19**, **Vite 8**, **Tailwind CSS v4**, and **Lucide React**:

```
frontend/
├── src/
│   ├── components/
│   │   ├── Header.jsx                 # System armed badge, backend status indicator
│   │   ├── Navigation.jsx             # 5-compartment segmented tab bar
│   │   ├── Compartment1_Scanner.jsx   # Live mic recording, canvas oscilloscope, verdict
│   │   ├── Compartment2_Physics.jsx   # Interactive SVG pitch curve, telemetry table
│   │   ├── Compartment3_Conversation.jsx # 4-stage funnel, transcript editor, tactic tags
│   │   ├── Compartment4_Verification.jsx # Out-of-band codeword simulator & questions
│   │   ├── Compartment5_Benchmarks.jsx   # Telephony degradation matrix & live runner
│   │   └── SidebarFusionControl.jsx   # Multi-modal calibration weight slider
│   ├── App.jsx                        # State orchestrator & API consumer
│   └── index.css                      # Tailwind v4, design tokens, pulse animations
├── vite.config.js                     # Tailwind plugin & backend proxy (/api -> 8000)
└── package.json
```

### Key Visual & Functional Upgrades:
1. **Real-Time HTML5 Canvas Oscilloscope:** When recording through the microphone, the browser connects to `AudioContext` and draws real-time oscillating sound wave bars across 128 frequency bins.
2. **Interactive SVG Pitch Contour ($F_0$):** Renders the pitch track over time with hover tooltips displaying frequency (Hz) at each second.
3. **Big Human Verdict Banners:**
   - `🟢 AUTHENTIC HUMAN VOICE` (Safe — Natural vocal physics, no coercion detected)
   - `🔴 DANGER: AI VOICE CLONE & SCAM` (High Threat — Synthetic vocal flatlining & financial urgency)
   - `🟡 CAUTION: SUSPICIOUS CONTENT` (Moderate Risk — Voice may sound human, but words are suspicious)
4. **Instant In-Page Audio Player:** Built-in playback control with seek bar and file metadata (16kHz PCM 16-bit).

---

## 4. Test Verification Matrix

All unit, integration, and full-stack API tests pass cleanly:

```
tests/test_fastapi_backend.py ............                               [ 22%]
tests/test_phase1.py ...                                                 [ 28%]
tests/test_phase2.py ...                                                 [ 33%]
tests/test_phase3.py ....                                                [ 41%]
tests/test_phase4.py ..                                                  [ 45%]
tests/test_phase5.py .                                                   [ 47%]
tests/test_robustness_quality.py ............................            [100%]

======================= 53 passed, 9 warnings in 26.40s ========================
```

---

## 5. How to Run the System

To start the full-stack system:

```bash
./start_servers.sh
```

Or manually:

```bash
# Backend (serves API & React App on port 8000):
./venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Open in browser:
http://localhost:8000/
```
