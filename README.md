# Debrief

Debrief turns meeting audio or transcripts into reviewable owner-by-owner tasks, then pushes confirmed work to Jira, Google Calendar, and Slack.

## What Works Now

- Paste a transcript, upload audio, or record from the browser.
- Audio transcription runs locally with `faster-whisper`.
- The backend is configured for CPU transcription with `int8`, so CUDA is not required.
- The host reviews extracted work per team member before anything is pushed.
- Each member can have separate delivery targets: Slack, Google Calendar, Jira, or any combination.
- The global delivery controls can force one platform setting across every selected member.
- Slack delivery posts the full transcript to the project channel and DMs selected assignees.
- Google Calendar requires an attendee email and no longer creates attendee-less events silently.
- Jira issue creation is wired, but live diagnostics currently show the configured Jira token/project access needs attention.

## Run The App

From the repo root:

```powershell
.\scripts\start_demo.ps1
```

Then open:

- Frontend: `http://localhost:5173`
- Backend health: `http://127.0.0.1:8005/health`
- Demo login: `leka` / `le124`

## Manual Setup

Backend:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .\backend
cd .\backend
..\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8005
```

Frontend:

```powershell
cd .\frontend
npm install
npm run dev
```

## Faster-Whisper

Debrief uses the open-source `faster-whisper` package through `backend/app/services/providers/transcription.py`.

Recommended local settings:

```env
FASTER_WHISPER_MODEL=small
FASTER_WHISPER_DEVICE=cpu
FASTER_WHISPER_COMPUTE_TYPE=int8
FASTER_WHISPER_LANGUAGE=
FASTER_WHISPER_BEAM_SIZE=5
FASTER_WHISPER_VAD_FILTER=true
```

Install FFmpeg if audio decoding fails:

```powershell
winget install Gyan.FFmpeg
```

## Integration Settings

Backend settings live in `backend/.env`.

Important keys:

```env
JIRA_BASE_URL=
JIRA_USER_EMAIL=
JIRA_API_TOKEN=
SLACK_BOT_TOKEN=
GOOGLE_CALENDAR_ID=
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
GOOGLE_OAUTH_REDIRECT_URI=http://127.0.0.1:8005/api/v1/auth/google/callback
```

Use the in-app project page to store each member's Jira email, calendar email, and Slack user ID.

## Delivery Behavior

- Jira creates one issue per selected task when that member has Jira enabled.
- Google Calendar creates one event per selected task when that member has Google Calendar enabled and a calendar email exists.
- Slack uploads the transcript once to the project channel, then DMs each member with Slack enabled.
- If a member-level platform toggle is off, that platform is skipped for that member only.

## Useful Checks

Run backend tests:

```powershell
cd .\backend
..\.venv\Scripts\python.exe -m pytest -p no:cacheprovider
```

Check Jira access:

```powershell
cd .\backend
..\.venv\Scripts\python.exe ..\scripts\jira_diagnostics.py
```

Run the confirmation smoke flow:

```powershell
py -3 scripts\test_confirm_flow.py
```

## Project Map

- `backend/app/api`: FastAPI routes
- `backend/app/services/integrations`: Jira, Google Calendar, Slack
- `backend/app/services/providers`: transcription and extraction providers
- `frontend/src`: React host console
- `scripts`: demo, smoke, and diagnostics helpers
- `docs`: architecture and API notes
