# Phase 2 Architecture

## Goal

Let the host review and correct extracted tasks in under 60 seconds before confirmation.

## What is now covered

1. Extraction returns the project employee directory alongside tasks.
2. The review screen uses confidence levels to determine field behavior:
   - `high`: locked
   - `medium`: editable and pre-filled
   - `low`: highlighted for quick correction
3. Assignees can be corrected from the known employee directory instead of typing internal IDs.
4. The host sees:
   - resolved transcripts
   - raw extraction JSON for debugging during demo
   - loaded employee directory
   - task review summary showing how many fields still need attention
5. Confirmation persists corrected tasks to the database and marks the meeting as confirmed.

## Still deferred

- Per-field audit history
- Bulk task actions
- Push-to-Jira and Slack delivery feedback in the review screen
- History page workflow for re-opening a prior meeting

