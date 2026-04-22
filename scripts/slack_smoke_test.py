import asyncio
import os
from datetime import date

from app.services.integrations.slack import SlackService


async def main() -> None:
    service = SlackService(bot_token=os.environ.get("SLACK_BOT_TOKEN"))
    recipients = [
        ("Rahul", "U0AUH5N144W"),
        ("Clara", "U0AUFQRDA5B"),
    ]
    for name, slack_user_id in recipients:
        result = await service.send_task_dm(
            slack_user_id=slack_user_id,
            title="Debrief Slack smoke test",
            deadline=date(2026, 4, 22),
            meeting_transcript=(
                "Smoke test transcript: verifying Debrief can send direct task "
                "messages with transcript context."
            ),
        )
        print(
            name,
            {
                "status": result.status,
                "error": result.error,
                "channel_id": result.channel_id,
                "message_ts": result.message_ts,
            },
        )


if __name__ == "__main__":
    asyncio.run(main())
