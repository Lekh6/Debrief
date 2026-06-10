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
