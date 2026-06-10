import asyncio

from app.services.integrations.google_calendar import GoogleCalendarService


class _TokenReadyCalendarService(GoogleCalendarService):
    async def _get_google_access_token(self, db, project_id):
        return "token"


def test_calendar_event_requires_attendee_email_before_push():
    service = _TokenReadyCalendarService()
    service.settings.google_calendar_id = "primary"

    result = asyncio.run(
        service.create_event(
            db=None,
            project_id="168d62d7-e74a-49e7-b81d-a8b83be46ea2",
            title="Review launch plan",
            description="Review the launch plan with the assignee.",
            due_date="2026-04-02",
            assignee_name="Rahul Mehta",
            assignee_email=None,
        )
    )

    assert result.status == "missing_attendee"
    assert result.event_id is None
