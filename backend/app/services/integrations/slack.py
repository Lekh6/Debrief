from dataclasses import dataclass


@dataclass
class SlackDeliveryResult:
    status: str
    error: str | None = None


class SlackService:
    async def send_task_dm(self, slack_user_id: str | None, title: str, jira_link: str | None) -> SlackDeliveryResult:
        return SlackDeliveryResult(
            status="not_configured",
            error="Slack integration is scaffolded but not configured yet.",
        )

    async def send_channel_summary(self, channel_id: str | None, task_count: int) -> SlackDeliveryResult:
        return SlackDeliveryResult(
            status="not_configured",
            error="Slack integration is scaffolded but not configured yet.",
        )

