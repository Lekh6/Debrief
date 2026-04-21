import asyncio
import json

import httpx

from app.core.config import get_settings


PROJECT_KEY = "KAN"
ASSIGNEE_ACCOUNT_ID = "712020:7a900cde-636a-4f29-8b18-c82e6b78634a"


async def main() -> None:
    settings = get_settings()
    auth = (settings.jira_user_email, settings.jira_api_token)
    base = settings.jira_base_url.rstrip("/")

    async with httpx.AsyncClient(timeout=30, auth=auth) as client:
        myself = await client.get(f"{base}/rest/api/3/myself", headers={"Accept": "application/json"})
        print("MYSELF", myself.status_code)
        print(myself.text[:2000])
        print()

        project = await client.get(f"{base}/rest/api/3/project/{PROJECT_KEY}", headers={"Accept": "application/json"})
        print("PROJECT", project.status_code)
        print(project.text[:2000])
        print()

        createmeta = await client.get(
            f"{base}/rest/api/3/issue/createmeta/{PROJECT_KEY}/issuetypes",
            headers={"Accept": "application/json"},
        )
        print("CREATEMETA", createmeta.status_code)
        print(createmeta.text[:4000])
        print()

        no_assignee_payload = {
            "fields": {
                "project": {"key": PROJECT_KEY},
                "summary": "Debrief no-assignee diagnostic",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Testing issue creation without assignee."}],
                        }
                    ],
                },
                "issuetype": {"name": "Task"},
                "duedate": "2026-04-07",
            }
        }
        no_assignee = await client.post(
            f"{base}/rest/api/3/issue",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=no_assignee_payload,
        )
        print("CREATE_NO_ASSIGNEE", no_assignee.status_code)
        print(no_assignee.text[:4000])
        print()

        with_assignee_payload = json.loads(json.dumps(no_assignee_payload))
        with_assignee_payload["fields"]["summary"] = "Debrief assignee diagnostic"
        with_assignee_payload["fields"]["assignee"] = {"accountId": ASSIGNEE_ACCOUNT_ID}
        with_assignee = await client.post(
            f"{base}/rest/api/3/issue",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=with_assignee_payload,
        )
        print("CREATE_WITH_ASSIGNEE", with_assignee.status_code)
        print(with_assignee.text[:4000])


if __name__ == "__main__":
    asyncio.run(main())
