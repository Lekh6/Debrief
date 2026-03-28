from dataclasses import dataclass

import httpx

from app.core.config import get_settings


@dataclass
class JiraCreateResult:
    issue_id: str | None
    status: str
    error: str | None = None


class JiraService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def create_issue(
        self,
        project_key: str | None,
        title: str,
        description: str,
        assignee_account_id: str | None,
        due_date: str | None,
    ) -> JiraCreateResult:
        if not self.settings.jira_base_url or not self.settings.jira_user_email or not self.settings.jira_api_token:
            return JiraCreateResult(
                issue_id=None,
                status="not_configured",
                error="Jira integration is scaffolded but not configured yet.",
            )
        if not project_key:
            return JiraCreateResult(issue_id=None, status="failed", error="Project is missing a Jira project key.")

        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": title,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": description or title,
                                }
                            ],
                        }
                    ],
                },
                "issuetype": {"name": "Task"},
            }
        }
        if assignee_account_id:
            payload["fields"]["assignee"] = {"id": assignee_account_id}
        if due_date:
            payload["fields"]["duedate"] = due_date

        endpoint = f"{self.settings.jira_base_url.rstrip('/')}/rest/api/3/issue"
        async with httpx.AsyncClient(timeout=30, auth=(self.settings.jira_user_email, self.settings.jira_api_token)) as client:
            response = await client.post(
                endpoint,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                json=payload,
            )

        if response.is_success:
            data = response.json()
            return JiraCreateResult(issue_id=data.get("key"), status="created")

        return JiraCreateResult(issue_id=None, status="failed", error=response.text)
