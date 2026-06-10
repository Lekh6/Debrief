## AI Context Log

This file captures significant implementation and debugging changes so context can be transferred across AI models.

### Project Snapshot

- Repo: `meetings`
- Stack: FastAPI backend (`backend/`), React + Vite frontend (`frontend/`)
- Primary flow: capture transcript/audio -> extraction pipeline -> host review -> delivery to Jira/Google Calendar/Slack

### Significant Changes

#### 2026-06-10 - Faster-whisper recording persistence and one-button meeting recording flow

- Backend transcription now stores every processed upload under root `recordings/` with unique timestamped filenames.
  - File: `backend/app/services/providers/transcription.py`
- Added `recordings/` to git ignore.
  - File: `.gitignore`
- Meeting pipeline now treats closing transcript/audio as optional and falls back to the meeting transcript when missing.
  - File: `backend/app/services/meeting_pipeline.py`
- Upload UI changed to a single large mic action for meeting capture (`Start meeting mic` / `Stop and transcribe`).
  - File: `frontend/src/components/UploadPanel.tsx`

#### 2026-06-10 - Review UI restructure and settings control

- Transcript and AI summary rendering changed from chunked cards to normal full text blocks.
  - File: `frontend/src/App.tsx`
- Host review now supports card rail + slide-out member detail panel.
  - File: `frontend/src/components/ConfirmationModal.tsx`
- Added profile preference toggle to enable/disable card-based review mode.
  - File: `frontend/src/App.tsx`
- Styling updated for card rail, slide panel, and mic button.
  - File: `frontend/src/styles/app.css`

#### 2026-06-10 - Dark mode and delivery debug toast hardening

- Added dark mode preference toggle in Profile settings.
  - File: `frontend/src/App.tsx`
- Added smooth theme color transitions between light/dark modes.
  - File: `frontend/src/styles/app.css`
- Delivery debug toast now includes explicit title/timestamp and handles empty results gracefully.
  - File: `frontend/src/App.tsx`
  - File: `frontend/src/styles/app.css`

#### 2026-06-10 - Dark mode rendering fix and confirm-toast messaging correction

- Dark mode now applies at `body` level so full-page backgrounds and overlays switch correctly, not just text.
  - File: `frontend/src/App.tsx`
  - File: `frontend/src/styles/app.css`
- Confirm debug toast fallback message now correctly reports when no tasks were included, instead of incorrectly saying no delivery targets were selected.
  - File: `frontend/src/App.tsx`

#### 2026-06-10 - Dark mode palette inversion and all-included confirm payload fix

- Dark mode palette was adjusted to invert the existing beige/dark theme into dark/beige with improved contrast and less visual obstruction.
  - File: `frontend/src/styles/app.css`
- Added `body.theme-dark` style coverage for shell/surfaces/form controls so dark mode updates full page visuals, not just text.
  - File: `frontend/src/styles/app.css`
- Confirm payload now includes all members marked `included` even when task text is empty, with safe fallback title/description generation.
  - File: `frontend/src/App.tsx`
- Jira token was rotated in local backend env as requested.
  - File: `backend/.env`

#### 2026-06-10 - Jira authentication recovery after token rotation

- Replaced Jira API token again and re-ran diagnostics; Jira auth, project access, createmeta, and issue creation all now succeed.
  - File: `backend/.env`
  - Validation: `scripts/jira_diagnostics.py` (`MYSELF 200`, `PROJECT 200`, `CREATE_* 201`)

#### 2026-06-10 - Transcript preview overlay + Jira project key guard + Slack DM content tightening

- Resolved meeting transcript preview now shows first ~7 lines with a full-screen themed "Show more" overlay and Back action.
  - File: `frontend/src/App.tsx`
  - File: `frontend/src/styles/app.css`
- Jira confirmation path now falls back to `KAN` project key when project key is missing, and demo fallback project keys were aligned to `KAN`.
  - File: `backend/app/api/meetings.py`
  - File: `frontend/src/App.tsx`
- Slack behavior now posts full transcript to project channel while DM payload is limited to task summary, due date, and task transcript details.
  - File: `backend/app/services/integrations/slack.py`
  - File: `backend/app/api/meetings.py`
  - File: `backend/tests/test_slack_integration.py`

#### 2026-06-10 - Runtime config refresh + Jira key normalization for confirm

- Settings cache was removed so backend reads updated `.env` values without requiring stale cached settings in-process.
  - File: `backend/app/core/config.py`
- Confirm flow now normalizes Jira project key to `KAN` to avoid failures from stale demo keys in stored projects.
  - File: `backend/app/api/meetings.py`
- Data Platform member diagnostics verified valid Slack DM user IDs for all three members; project channel ID still resolves `channel_not_found`.
  - Validation: `conversations.open` for `U0AUH5N144W`, `U0AUFQRDA5B`, `U0AQW0NCQAW`

#### 2026-06-10 - Slack transcript/header format reset and DM delivery rules

- Slack project-channel transcript payload now includes formatted header/footer separators, meeting topic, date, and member list, with transcript lines rendered as bullets.
  - File: `backend/app/services/integrations/slack.py`
- Slack DMs now include meeting topic header, what-to-do summary, due date, and task transcript only.
  - File: `backend/app/services/integrations/slack.py`
- Confirm flow now skips Slack DMs for tasks with empty transcript text, while still allowing other delivery targets.
  - File: `backend/app/api/meetings.py`
- Updated Slack tests and smoke script for new payload shape.
  - File: `backend/tests/test_slack_integration.py`
  - File: `scripts/slack_smoke_test.py`

#### 2026-06-10 - Slack DM route guard and status clarity

- Slack DM flow now rejects non-user identifiers (`C*`, `G*`, `D*`) in member `slack_user_id` to prevent channel routing mistakes.
  - File: `backend/app/services/integrations/slack.py`
- Slack DM send now verifies `conversations.open` returned a DM channel (`D*`) before posting.
  - File: `backend/app/services/integrations/slack.py`
- Confirm response now always reports both channel and DM delivery outcomes when either path fails (e.g. `channel_failed;dm_delivered`).
  - File: `backend/app/api/meetings.py`

#### 2026-06-10 - Slack DM end-to-end routing diagnostics and destination verification

- Added deterministic Slack delivery diagnostics fields (`intended_mode`, recipient, conversations-open channel, final channel, raw response) to Slack delivery results.
  - File: `backend/app/services/integrations/slack.py`
- Added structured route logging around `conversations.open` and `chat.postMessage` for DM/channel sends.
  - File: `backend/app/services/integrations/slack.py`
- Added routing tests verifying DM path uses `conversations.open -> D* -> chat.postMessage(D*)` and channel path posts to `C*` channel IDs.
  - File: `backend/tests/test_slack_integration.py`
- Added executable diagnostic script that prints real DM and channel destination evidence for current workspace/project configuration.
  - File: `scripts/slack_route_diagnostics.py`

### Integration Diagnostics (latest run)

- Jira diagnostics currently return authentication/authorization failures (`401`, project permission errors).
- Slack direct-message smoke test succeeds for configured users.
- Google Calendar delivery in confirm flow fails with service-account attendee invite restriction unless OAuth/domain-wide delegation is used.

### Known Follow-ups

- Jira credentials/project permissions need external account-side fix.
- Google Calendar attendee invite support needs OAuth-connected project credential or domain-wide delegation.
- Keep this file updated whenever a significant feature, bugfix, integration behavior, or architectural decision changes.
