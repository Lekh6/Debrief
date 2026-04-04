import asyncio

import httpx

from app.core.config import get_settings


async def main() -> None:
    settings = get_settings()
    key = "KAN"
    async with httpx.AsyncClient(
        timeout=30,
        auth=(settings.jira_user_email, settings.jira_api_token),
    ) as client:
        response = await client.get(
            f"{settings.jira_base_url.rstrip('/')}/rest/api/3/project/{key}",
            headers={"Accept": "application/json"},
        )
        print(response.status_code)
        print(response.text[:4000])


if __name__ == "__main__":
    asyncio.run(main())
