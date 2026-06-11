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

#### 2026-06-11 - Channel ID prefix guard + decoupled delivery status

- `publish_transcript` now validates channel ID starts with `C` before posting, mirroring the D-prefix guard in `send_task_dm`.
  - File: `backend/app/services/integrations/slack.py`
- `confirm_meeting_tasks` no longer merges channel+DM status into a single `"delivered"`; channel and DM outcomes are always reported independently (e.g. `channel_delivered;dm_delivered`, `channel_failed;dm_missing_recipient`).
  - File: `backend/app/api/meetings.py`
- Frontend Slack status parsing updated for the always-combined format.
  - File: `frontend/src/App.tsx`
- Added `test_channel_publish_rejects_non_channel_prefix` verifying C-prefix guard with zero API calls.
  - File: `backend/tests/test_slack_integration.py`

#### 2026-06-11 - UI cleanup + Slack message separators + API fixes

- Removed README page from top navigation bar and removed accent picker from Profile settings.
  - File: `frontend/src/App.tsx`
  - File: `frontend/src/styles/app.css`
- Fixed `project_id` type from `str` to `UUID` in `get_project` and `create_project_employee` endpoints for proper FastAPI validation.
  - File: `backend/app/api/projects.py`
- Fixed dark mode accent colors: `--accent` and `--accent-2` now defined in `body.theme-dark` to prevent invisible ink-accent text on dark backgrounds.
  - File: `frontend/src/styles/app.css`
- Added dark mode cursor glow: a large radial-gradient blur div that follows the mouse in dark mode for a subtle light halo around the cursor.
  - File: `frontend/src/App.tsx`
  - File: `frontend/src/styles/app.css`
- Replaced `mix-blend-mode: multiply` on `body::before` with `opacity: 0.4` to reduce rendering artifacts.
  - File: `frontend/src/styles/app.css`
- Added smooth transitions on `.panel`, `.banner`, and `.app-shell` for theme switching and layout changes.
  - File: `frontend/src/styles/app.css`
- Slack transcript and DM messages now include `=====` separator banners to clearly distinguish channel transcript posts from individual task-assignment DMs.
  - File: `backend/app/services/integrations/slack.py`
  - File: `backend/tests/test_slack_integration.py`

#### 2026-06-11 — Toggle switches, dark mode polish, logout confirm, Profile→Settings, 422 fix, refresh isolation

- Added `backend/app/api/__init__.py` (empty) for Python package resolution.
  - File: `backend/app/api/__init__.py`
- `addProjectMember` now parses FastAPI 422 `detail` arrays into readable error strings.
  - File: `frontend/src/lib/api.ts`
- `handleAddMember` now clears error/success state before the try block and isolates `onRefresh()` failure via `.catch(() => {})` so success state is never overwritten by polling errors.
  - File: `frontend/src/App.tsx`
- Profile nav button and Preferences page eyebrow renamed from "Profile" to "Settings".
  - File: `frontend/src/App.tsx`
- Logout now shows a confirmation overlay with a red `danger-button` and Cancel option.
  - File: `frontend/src/App.tsx`
  - File: `frontend/src/styles/app.css`
- Added floating moon/sun dark mode toggle button (fixed top-right, crescent/sun unicode symbols) with explicit `color: var(--ink)` to ensure visibility in dark mode.
  - File: `frontend/src/App.tsx`
  - File: `frontend/src/styles/app.css`
- All native `<input type="checkbox">` replaced with custom animated toggle switches:
  - Profile preferences (compact mode, reduce motion, card review, dark mode)
  - ConfirmationModal member include (both card-rail and grid views)
  - Uses `.toggle-switch` / `.toggle-track` / `.toggle-thumb` with sliding transform on `:checked`.
  - File: `frontend/src/App.tsx`
  - File: `frontend/src/components/ConfirmationModal.tsx`
  - File: `frontend/src/styles/app.css`
- Added "Include" label text beside each member toggle in ConfirmationModal.
  - File: `frontend/src/components/ConfirmationModal.tsx`
  - File: `frontend/src/styles/app.css`
- CSS fixes/consistency:
  - Background grid `background-size` unified to 18px in both modes (was 20px in dark).
  - `.transcript-content` and `.summary-row p` color overridden in dark mode to `var(--ink)` (was invisible `var(--bg-soft)` on black panel).
  - `.member-select-card` and `.member-editor` borders use `var(--line)` instead of hardcoded `rgba(5,5,5,…)`.
  - Removed redundant `body.theme-dark .app-shell` transition block.
  - File: `frontend/src/styles/app.css`

#### 2026-06-11 — Color consistency: eliminate all green from both modes

- Light mode `--accent` changed from `#7c9f84` (olive green) to `#c4966e` (warm sand/tan). No green remains in light mode.
- Dark mode `--accent` changed from `#8fb899` (green) to `#dacf6a` (warm sand/yellow). No green remains in dark mode.
- Dark mode `--accent-2` changed from `#dacf6a` back to `#cf7e6d` (terracotta, same as light mode).
- All hardcoded green rgba values updated to match new accent colors:
  - Body background radial blobs (light + dark)
  - `input:focus` box-shadows (light + dark)
  - `body.theme-dark .primary-button` box-shadows
- File: `frontend/src/styles/app.css`

#### 2026-06-11 — Nav restructure, UploadPanel copy, debug extraction, dark mode beige-ification

- Nav bar restructured:
  - Removed "debrief" brand-mark pill from inside the nav bar.
  - Added `.page-header` above the nav: `<h1 class="site-title">debrief</h1>` (font-only text logo in top-left) + `<p class="current-tab">` showing current page name below it.
  - Removed `.status-ribbon` entirely (signed-in-as, tab label, projects-loaded text).
  - Renamed "Review" nav button → "Home".
  - `AppPage` type changed from `"review" | "teams" | "profile"` to `"home" | "teams" | "profile"`.
  - File: `frontend/src/App.tsx`
  - File: `frontend/src/styles/app.css` (added `.page-header`, `.site-title`, `.current-tab`)
- UploadPanel copy changes:
  - Removed "Phase 1 Intake" eyebrow heading.
  - Changed subtitle to: "Record live meeting audio or upload files. Automatically updates slack, jira and google cal."
  - Changed `<option>` placeholder from "Select demo project" → "Project".
  - File: `frontend/src/components/UploadPanel.tsx`
- Debug code extracted to `frontend/src/lib/debug.tsx`:
  - Created separate file with `DEBUG_ENABLED = false` flag.
  - Contains `PushToastState` interface, `buildPushToast()`, `DebugPushToast` component, `DebugBanners` component — all guarded by `DEBUG_ENABLED`.
  - To re-enable: set `DEBUG_ENABLED = true` and import/use the components in App.tsx.
  - Stripped all delivery-status tracking (`jira_status`, `slack_delivery_status`, etc.) from `handleConfirm` in App.tsx.
  - Removed `pushToast`, `successMessage` state and all related JSX from App.tsx.
  - Keep `error` state for critical extraction/confirm failures only.
  - File: `frontend/src/lib/debug.tsx`
  - File: `frontend/src/App.tsx`
- Dark mode accent adjusted more beige/less yellow:
  - `--accent` changed from `#dacf6a` (yellow sand) → `#c9b692` (warm beige/tan).
  - All hardcoded rgba references updated from `218, 207, 106` → `201, 182, 146`.
  - File: `frontend/src/styles/app.css`

### Integration Diagnostics (latest run)

- Jira diagnostics currently return authentication/authorization failures (`401`, project permission errors).
- Slack direct-message smoke test succeeds for configured users.
- Google Calendar delivery in confirm flow fails with service-account attendee invite restriction unless OAuth/domain-wide delegation is used.

### Known Follow-ups

- Jira credentials/project permissions need external account-side fix.
- Google Calendar attendee invite support needs OAuth-connected project credential or domain-wide delegation.
- Keep this file updated whenever a significant feature, bugfix, integration behavior, or architectural decision changes.
