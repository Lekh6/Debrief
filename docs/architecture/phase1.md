# Phase 1 Architecture

## Goal

Validate that the system can reliably turn meeting context plus a short host closing statement into structured tasks before we invest in OAuth, Jira, Slack, and history polish.

## Current flow

1. The frontend submits `project_id` plus either transcripts or uploaded files.
2. The backend resolves transcripts:
   - Uses pasted text immediately when provided.
   - Uses the Whisper-compatible endpoint when audio is uploaded and `WHISPER_BASE_URL` is configured.
3. The backend loads project employees from the database.
4. The extraction service:
   - Uses the Gemini `generateContent` API when configured and heuristic mode is disabled.
   - Falls back to a deterministic extractor so the team can develop without waiting on model credentials.
5. Extracted tasks are stored as a pending meeting.
6. The host reviews and confirms tasks in the frontend.
7. Confirmation rewrites the meeting tasks in the database and marks the meeting as confirmed.

## Planned upgrades

- Replace startup `create_all()` with Alembic migrations.
- Add a provider abstraction layer if you later want Anthropic or another model family alongside Gemini.
- Add Jira and Slack retry policies with per-task delivery records.
- Add a history page view backed by live Jira refresh rather than persisted task status only.
