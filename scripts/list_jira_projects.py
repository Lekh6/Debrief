import asyncio

import httpx

from app.core.config import get_settings


async def main() -> None:
    settings = get_settings()
    async with httpx.AsyncClient(
        timeout=30,
        auth=(settings.jira_user_email, settings.jira_api_token),
    ) as client:
        response = await client.get(
            f"{settings.jira_base_url.rstrip('/')}/rest/api/3/project/search",
            headers={"Accept": "application/json"},
            params={"maxResults": 100},
        )
        print(response.status_code)
        data = response.json()
        print(data)
        for project in data.get("values", []):
            print(f"{project.get('key')} | {project.get('name')} | {project.get('id')}")


if __name__ == "__main__":
    asyncio.run(main())
