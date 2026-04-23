# Debrief - Post-Meeting Task Automation

Debrief turns meeting transcripts into reviewable tasks, then pushes confirmed tasks to Jira, Google Calendar, and Slack.

## Current project state

- Backend: FastAPI + SQLAlchemy (`backend/`)
- Frontend: React + TypeScript + Vite (`frontend/`)
- Local transcription: `faster-whisper` (audio -> transcript)
- Integrations wired in confirm flow:
  - Jira issue creation
  - Google Calendar event creation
  - Slack DM delivery to assignees
- Extraction supports Gemini and a heuristic fallback

## Easiest way to run (Windows demo mode)

From the repo root:

```powershell
.\scripts\start_demo.ps1
```

This starts backend and frontend in separate PowerShell windows.

- Backend URL: `http://127.0.0.1:8005`
- Frontend URL: `http://localhost:5173`
- Demo login: `leka` / `le124`

## Manual run (recommended for development)

### 1) Backend setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .\backend
```

### 2) Backend run

```powershell
cd .\backend
..\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8005
```

### 3) Frontend setup + run

In a second terminal:

```powershell
cd .\frontend
npm install
npm run dev
```

The frontend uses `frontend/.env` and points to `http://127.0.0.1:8005/api/v1` by default.

## Environment config

- Backend reads settings from `backend/.env`
- Use `backend/.env.example` as reference
- Faster-whisper is local and configured by:
  - `FASTER_WHISPER_MODEL` (for example `small`, `medium`, `large-v3`)
  - `FASTER_WHISPER_DEVICE` (`auto`, `cpu`, `cuda`)
  - `FASTER_WHISPER_COMPUTE_TYPE` (`int8`, `int8_float16`, `float16`, `float32`)
  - `FASTER_WHISPER_LANGUAGE` (leave empty for auto-detect, or set `en`)
  - `FASTER_WHISPER_BEAM_SIZE`
  - `FASTER_WHISPER_VAD_FILTER`
- Key integration toggles:
  - `AUTO_CREATE_JIRA_ON_CONFIRM`
  - `AUTO_CREATE_GOOGLE_CALENDAR_ON_CONFIRM`
  - `AUTO_NOTIFY_SLACK_ON_CONFIRM`

Note: the frontend confirm modal also sends explicit delivery targets, so those UI choices take priority per request.

## Seed demo data (optional)

After backend is running:

```powershell
cd .\backend
..\.venv\Scripts\python -m app.seed_demo
```

## Project layout

- `backend/` API routes, extraction pipeline, integrations, DB models
- `frontend/` host review UI + team management
- `scripts/` diagnostics and smoke scripts
- `docs/` architecture and API notes

## Troubleshooting

- Install system dependency for audio decoding:

```powershell
winget install Gyan.FFmpeg
```

- If backend fails with Google auth import errors, install missing dependencies in the venv:

```powershell
.\.venv\Scripts\python -m pip install requests
```

- On first transcription run, faster-whisper downloads model files locally, so the first request can be slower.

- If extraction fails due to model/provider availability, switch to heuristic mode in `backend/.env`:

```env
USE_HEURISTIC_EXTRACTOR=true
```
