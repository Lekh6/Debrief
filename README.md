# Post-Meeting Task Automation Tool

Greenfield scaffold for the post-meeting task automation workflow described in the project spec. The repository is organized to get Phase 1 moving quickly while leaving clean seams for Jira, Slack, OAuth, and richer transcription providers.

## Workspace layout

- `backend/` FastAPI application, extraction pipeline, SQLAlchemy models, and integration stubs
- `frontend/` React + TypeScript confirmation UI
- `docs/` short architecture and API notes

## What is implemented

- Project, employee, meeting, and task data models
- Extraction endpoint that accepts transcripts now and audio uploads when Whisper is configured
- Gemini extraction path with JSON-structured responses and heuristic fallback for local development
- Confidence-aware task extraction response shape
- Meeting confirmation endpoint and meeting history endpoint
- Lightweight React UI for upload, review, inline edit, employee-based assignee correction, and confirm
- Google Calendar integration is about 90% working:
  event creation and deadline pushes work, OAuth2 flow is scaffolded, and the main remaining blocker is Google OAuth test-user / verification setup
- Integration seams for Jira and Slack so Phase 3 and Phase 4 can slot in without a rewrite

## Current assumptions

- We are prioritizing Phase 1 and early Phase 2 over production auth/integration work
- Audio upload is supported at the API boundary, but real transcription requires a configured Whisper endpoint
- If Gemini is not configured, the backend falls back to a deterministic heuristic extractor so development can continue locally

## Backend quick start

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .
uvicorn app.main:app --reload
```

Seed a demo project after the API is running:

```bash
cd backend
python -m app.seed_demo
```

The seed now creates 4 independent demo projects with 11 employees total so you can prove project-ID scoping in the UI and integration flow.

## Frontend quick start

```bash
cd frontend
npm install
npm run dev
```

## Next milestones

1. Validate extraction quality against real meeting transcripts.
2. Add Jira OAuth and issue creation.
3. Add Slack OAuth, DMs, and channel summaries.
4. Finish Google OAuth testing setup so attendee invites send through the connected host account.
5. Build the meeting history page with live Jira status pulls.
6. Move from `create_all()` bootstrapping to migrations.
