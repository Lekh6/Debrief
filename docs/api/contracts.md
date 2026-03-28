# API Contracts

## `POST /api/v1/projects`

Creates a project and an optional employee directory.

Example request:

```json
{
  "name": "Website Redesign",
  "jira_project_key": "WR",
  "slack_channel_id": "C123456",
  "employees": [
    {
      "name": "John Carter",
      "jira_account_id": "abc123",
      "slack_user_id": "U123"
    }
  ]
}
```

## `POST /api/v1/meetings/extract`

Multipart form endpoint.

Fields:

- `project_id` required
- `meeting_transcript` optional if `meeting_audio` is sent
- `closing_transcript` optional if `closing_audio` is sent
- `meeting_audio` optional if `meeting_transcript` is sent
- `closing_audio` optional if `closing_transcript` is sent

Response includes:

- persisted `meeting_id`
- resolved transcripts
- extracted tasks
- `extraction_mode` (`heuristic` or `llm`)

## `POST /api/v1/meetings/{meeting_id}/confirm`

Accepts edited tasks from the host. The backend matches assignees first by `assignee_id`, then by `assignee_name`.

## `GET /api/v1/meetings?project_id=<uuid>`

Returns saved meetings for the given project, newest first.
