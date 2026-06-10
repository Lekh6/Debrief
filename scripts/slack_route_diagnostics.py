import asyncio
import os
from datetime import datetime, timezone

from app.services.integrations.slack import SlackService


async def main() -> None:
    service = SlackService(bot_token=os.environ.get("SLACK_BOT_TOKEN"))

    dm_result = await service.send_task_dm(
        slack_user_id="U0AUH5N144W",
        meeting_topic="Data Platform Upgrade",
        title="Routing diagnostics DM",
        description="This message validates DM routing through conversations.open.",
        deadline=None,
    )
    print("DM_RESULT", dm_result)

    channel_result = await service.publish_transcript(
        channel_id="C-DEMO-DATA",
        meeting_topic="Data Platform Upgrade",
        meeting_transcript="Routing diagnostics transcript line one. line two.",
        meeting_date=datetime.now(timezone.utc),
        member_names=["Rahul Mehta", "Clara Zhou", "Eva Stone"],
    )
    print("CHANNEL_RESULT", channel_result)


if __name__ == "__main__":
    asyncio.run(main())
