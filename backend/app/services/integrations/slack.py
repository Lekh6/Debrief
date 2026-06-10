import asyncio
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import httpx

from app.core.config import get_settings


@dataclass
class SlackDeliveryResult:
    status: str
    error: str | None = None
    channel_id: str | None = None
    message_ts: str | None = None


class SlackService:
    def __init__(self, bot_token: str | None = None) -> None:
        settings = get_settings()
        self.bot_token = bot_token if bot_token is not None else settings.slack_bot_token

    async def send_task_dm(
        self,
        slack_user_id: str | None,
        meeting_topic: str,
        title: str,
        description: str,
        deadline: date | None,
    ) -> SlackDeliveryResult:
        readiness_error = self._validate_ready()
        if readiness_error:
            return readiness_error
        normalized_user_id = self._normalize_user_id(slack_user_id or "")
        if not normalized_user_id:
            return SlackDeliveryResult(
                status="missing_recipient",
                error="Assignee is missing a Slack user ID.",
            )
        task_transcript = description.strip()
        if not task_transcript:
            return SlackDeliveryResult(
                status="missing_task",
                error="Task details are required before sending task DMs.",
            )

        open_result = await self._call_slack_api("conversations.open", {"users": normalized_user_id})
        if isinstance(open_result, SlackDeliveryResult):
            return open_result

        dm_channel_id = (open_result.get("channel") or {}).get("id")
        if not dm_channel_id:
            return SlackDeliveryResult(status="failed", error="Slack did not return a DM channel ID.")
        if not dm_channel_id.startswith("D"):
            return SlackDeliveryResult(
                status="failed",
                error=f"Slack returned a non-DM channel ({dm_channel_id}) for recipient.",
            )

        message = self._build_task_dm_message(meeting_topic, title, description, deadline)
        post_result = await self._call_slack_api(
            "chat.postMessage",
            {
                "channel": dm_channel_id,
                "text": message,
                "mrkdwn": True,
                "unfurl_links": False,
                "unfurl_media": False,
            },
        )
        if isinstance(post_result, SlackDeliveryResult):
            return post_result

        return SlackDeliveryResult(
            status="delivered",
            channel_id=post_result.get("channel") or dm_channel_id,
            message_ts=post_result.get("ts"),
        )

    async def publish_transcript(
        self,
        channel_id: str | None,
        meeting_topic: str,
        meeting_transcript: str,
        meeting_date: datetime,
        member_names: list[str],
        closing_transcript: str | None = None,
    ) -> SlackDeliveryResult:
        readiness_error = self._validate_ready()
        if readiness_error:
            return readiness_error
        normalized_channel_id = (channel_id or "").strip()
        if not normalized_channel_id:
            return SlackDeliveryResult(
                status="missing_channel",
                error="Project is missing a Slack channel ID.",
            )
        if not meeting_transcript.strip():
            return SlackDeliveryResult(
                status="missing_transcript",
                error="Meeting transcript is required before publishing to Slack.",
            )

        message = self._build_transcript_message(
            meeting_topic=meeting_topic,
            meeting_transcript=meeting_transcript,
            meeting_date=meeting_date,
            member_names=member_names,
            closing_transcript=closing_transcript,
        )
        post_result = await self._call_slack_api(
            "chat.postMessage",
            {
                "channel": normalized_channel_id,
                "text": message,
                "mrkdwn": True,
                "unfurl_links": False,
                "unfurl_media": False,
            },
        )
        if isinstance(post_result, SlackDeliveryResult):
            return post_result

        return SlackDeliveryResult(
            status="delivered",
            channel_id=post_result.get("channel") or normalized_channel_id,
            message_ts=post_result.get("ts"),
        )

    def _validate_ready(self) -> SlackDeliveryResult | None:
        if not self.bot_token:
            return SlackDeliveryResult(
                status="not_configured",
                error="Slack bot token is missing.",
            )
        if self.bot_token.startswith("xapp-"):
            return SlackDeliveryResult(
                status="invalid_token_type",
                error="Slack app-level tokens cannot call chat.postMessage. Use the Bot User OAuth token that starts with xoxb-.",
            )
        return None

    def _build_task_dm_message(self, meeting_topic: str, title: str, description: str, deadline: date | None) -> str:
        deadline_text = deadline.isoformat() if deadline else "Not specified"
        return "\n".join(
            [
                f"Meeting topic: {meeting_topic}",
                "",
                f"What you should do: {title}",
                f"Deadline: {deadline_text}",
                "",
                "Task transcript:",
                description.strip(),
            ]
        )

    def _build_transcript_message(
        self,
        meeting_topic: str,
        meeting_transcript: str,
        meeting_date: datetime,
        member_names: list[str],
        closing_transcript: str | None = None,
    ) -> str:
        date_text = meeting_date.date().isoformat()
        member_text = ", ".join(sorted({name.strip() for name in member_names if name and name.strip()})) or "Not specified"
        parts = [
            "========================================",
            f"*Meeting topic:* {meeting_topic}",
            f"*Date:* {date_text}",
            f"*Members:* {member_text}",
            "========================================",
            "",
            "*Meeting transcript:*",
            self._format_transcript_block(meeting_transcript),
        ]
        if closing_transcript and closing_transcript.strip():
            parts.extend(["", "*Closing transcript:*", self._format_transcript_block(closing_transcript)])
        parts.extend(["", "========================================"])
        return "\n".join(parts)

    def _format_transcript_block(self, transcript: str) -> str:
        lines = [line.strip() for line in transcript.replace("\r", "\n").split("\n") if line.strip()]
        if len(lines) <= 1:
            sentence_parts = [segment.strip() for segment in transcript.split(".") if segment.strip()]
            lines = sentence_parts
        return "\n".join(f"- {line}" for line in lines)

    def _normalize_user_id(self, slack_user_id: str) -> str:
        normalized = slack_user_id.strip()
        if normalized.startswith("<@") and normalized.endswith(">"):
            normalized = normalized[2:-1]
        if "|" in normalized:
            normalized = normalized.split("|", 1)[0]
        normalized = normalized.lstrip("@").strip()
        if normalized.upper().startswith(("C", "G", "D")):
            return ""
        return normalized

    async def _call_slack_api(
        self,
        method: str,
        payload: dict[str, Any],
        http_method: str = "POST",
    ) -> dict[str, Any] | SlackDeliveryResult:
        url = f"https://slack.com/api/{method}"
        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json; charset=utf-8",
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                for attempt in range(2):
                    if http_method == "GET":
                        response = await client.get(url, headers=headers, params=payload)
                    else:
                        response = await client.post(url, headers=headers, json=payload)

                    if response.status_code == 429 and attempt == 0:
                        retry_after = self._retry_after_seconds(response.headers.get("Retry-After"))
                        await asyncio.sleep(retry_after)
                        continue

                    if not response.is_success:
                        return SlackDeliveryResult(status="failed", error=response.text)

                    data = response.json()
                    if data.get("ok"):
                        return data
                    return SlackDeliveryResult(status="failed", error=str(data.get("error") or data))
        except Exception as exc:
            return SlackDeliveryResult(status="failed", error=str(exc))

        return SlackDeliveryResult(status="failed", error="Slack request failed after retry.")

    def _retry_after_seconds(self, value: str | None) -> float:
        try:
            return min(max(float(value or 1), 0), 5)
        except ValueError:
            return 1
