import asyncio
from datetime import date

from app.services.integrations.slack import SlackService


def test_task_dm_message_matches_required_format():
    service = SlackService(bot_token="xoxb-test")

    message = service._build_task_dm_message(
        "Send launch plan",
        date(2026, 4, 30),
        "Rahul agreed to send the launch plan.",
    )

    assert message == (
        "Task: Send launch plan\n"
        "Deadline: 2026-04-30\n"
        "\n"
        "Meeting transcript:\n"
        "Rahul agreed to send the launch plan."
    )


def test_publish_transcript_reports_missing_configuration_before_network_call():
    service = SlackService(bot_token="")

    result = asyncio.run(
        service.send_task_dm(
            slack_user_id="U123",
            title="Send launch plan",
            deadline=None,
            meeting_transcript="Full meeting transcript.",
        )
    )

    assert result.status == "not_configured"


def test_app_level_token_is_rejected_before_network_call():
    service = SlackService(bot_token="xapp-test")

    result = asyncio.run(
        service.send_task_dm(
            slack_user_id="U123",
            title="Send launch plan",
            deadline=None,
            meeting_transcript="Full meeting transcript.",
        )
    )

    assert result.status == "invalid_token_type"


def test_slack_user_id_normalization_accepts_mentions():
    service = SlackService(bot_token="xoxb-test")

    assert service._normalize_user_id("<@U123|Rahul>") == "U123"
    assert service._normalize_user_id("@U456") == "U456"
