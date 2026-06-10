import asyncio
from datetime import date
from datetime import datetime

from app.services.integrations.slack import SlackService


def test_task_dm_message_matches_required_format():
    service = SlackService(bot_token="xoxb-test")

    message = service._build_task_dm_message(
        "Data Platform Upgrade",
        "Send launch plan",
        "Rahul agreed to send the launch plan.",
        date(2026, 4, 30),
    )

    assert message == (
        "Meeting topic: Data Platform Upgrade\n"
        "\n"
        "What you should do: Send launch plan\n"
        "Deadline: 2026-04-30\n"
        "\n"
        "Task transcript:\n"
        "Rahul agreed to send the launch plan."
    )


def test_publish_transcript_reports_missing_configuration_before_network_call():
    service = SlackService(bot_token="")

    result = asyncio.run(
        service.send_task_dm(
            slack_user_id="U123",
            meeting_topic="Data Platform Upgrade",
            title="Send launch plan",
            description="Rahul agreed to send the launch plan.",
            deadline=None,
        )
    )

    assert result.status == "not_configured"


def test_transcript_message_includes_meeting_and_closing_transcripts():
    service = SlackService(bot_token="xoxb-test")

    message = service._build_transcript_message(
        meeting_topic="Data Platform Upgrade",
        meeting_transcript="Rahul will review the migration plan.",
        meeting_date=datetime(2026, 6, 10, 9, 30, 0),
        member_names=["Rahul Mehta", "Clara Zhou"],
        closing_transcript="Clara will validate analytics mapping.",
    )

    assert message == (
        "========================================\n"
        "*Meeting topic:* Data Platform Upgrade\n"
        "*Date:* 2026-06-10\n"
        "*Members:* Clara Zhou, Rahul Mehta\n"
        "========================================\n"
        "\n"
        "*Meeting transcript:*\n"
        "- Rahul will review the migration plan\n"
        "\n"
        "*Closing transcript:*\n"
        "- Clara will validate analytics mapping\n"
        "\n"
        "========================================"
    )


def test_publish_transcript_requires_project_channel():
    service = SlackService(bot_token="xoxb-test")

    result = asyncio.run(
        service.publish_transcript(
            channel_id=None,
            meeting_topic="Data Platform Upgrade",
            meeting_transcript="Full meeting transcript.",
            meeting_date=datetime(2026, 6, 10, 9, 30, 0),
            member_names=["Rahul Mehta", "Clara Zhou"],
        )
    )

    assert result.status == "missing_channel"


def test_app_level_token_is_rejected_before_network_call():
    service = SlackService(bot_token="xapp-test")

    result = asyncio.run(
        service.send_task_dm(
            slack_user_id="U123",
            meeting_topic="Data Platform Upgrade",
            title="Send launch plan",
            description="Rahul agreed to send the launch plan.",
            deadline=None,
        )
    )

    assert result.status == "invalid_token_type"


def test_slack_user_id_normalization_accepts_mentions():
    service = SlackService(bot_token="xoxb-test")

    assert service._normalize_user_id("<@U123|Rahul>") == "U123"
    assert service._normalize_user_id("@U456") == "U456"


class _RoutingProbeSlackService(SlackService):
    def __init__(self, responses):
        super().__init__(bot_token="xoxb-test")
        self.responses = responses
        self.calls = []

    async def _call_slack_api(self, method, payload, http_method="POST"):
        self.calls.append((method, payload))
        value = self.responses.get(method)
        if callable(value):
            return value(payload)
        return value


def test_dm_uses_conversations_open_then_posts_to_d_channel():
    service = _RoutingProbeSlackService(
        responses={
            "conversations.open": {"ok": True, "channel": {"id": "D123"}},
            "chat.postMessage": {"ok": True, "channel": "D123", "ts": "1.2"},
        }
    )

    result = asyncio.run(
        service.send_task_dm(
            slack_user_id="U123",
            meeting_topic="Data Platform Upgrade",
            title="Send launch plan",
            description="Task transcript",
            deadline=None,
        )
    )

    assert result.status == "delivered"
    assert result.conversations_open_channel_id == "D123"
    assert result.final_channel_id == "D123"
    assert service.calls[0][0] == "conversations.open"
    assert service.calls[1][0] == "chat.postMessage"
    assert service.calls[1][1]["channel"] == "D123"


def test_channel_publish_posts_to_project_channel_id():
    service = _RoutingProbeSlackService(
        responses={
            "chat.postMessage": {"ok": True, "channel": "C999", "ts": "2.3"},
        }
    )

    result = asyncio.run(
        service.publish_transcript(
            channel_id="C999",
            meeting_topic="Data Platform Upgrade",
            meeting_transcript="Line one. Line two.",
            meeting_date=datetime(2026, 6, 10, 9, 30, 0),
            member_names=["Rahul Mehta"],
        )
    )

    assert result.status == "delivered"
    assert result.final_channel_id == "C999"
    assert service.calls[0][0] == "chat.postMessage"
    assert service.calls[0][1]["channel"] == "C999"


def test_dm_fails_when_conversations_open_returns_non_dm_channel():
    service = _RoutingProbeSlackService(
        responses={
            "conversations.open": {"ok": True, "channel": {"id": "C123"}},
        }
    )

    result = asyncio.run(
        service.send_task_dm(
            slack_user_id="U123",
            meeting_topic="Data Platform Upgrade",
            title="Send launch plan",
            description="Task transcript",
            deadline=None,
        )
    )

    assert result.status == "failed"
    assert "non-DM channel" in (result.error or "")
    assert len(service.calls) == 1
