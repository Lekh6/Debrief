import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx
from google.auth.transport.requests import Request
from google.oauth2 import service_account

from app.core.config import get_settings


@dataclass
class GoogleCalendarResult:
    event_id: str | None
    status: str
    error: str | None = None


class GoogleCalendarService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def create_event(self, title: str, description: str, due_date: str | None, assignee_name: str | None) -> GoogleCalendarResult:
        if not self.settings.google_service_account_json or not self.settings.google_calendar_id:
            return GoogleCalendarResult(
                event_id=None,
                status="not_configured",
                error="Google Calendar integration is not configured yet.",
            )

        event_start, event_end = self._build_times(due_date)
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(self.settings.google_service_account_json),
            scopes=["https://www.googleapis.com/auth/calendar"],
        )
        credentials.refresh(Request())

        payload = {
            "summary": title,
            "description": description,
            "start": {"dateTime": event_start.isoformat()},
            "end": {"dateTime": event_end.isoformat()},
        }
        if assignee_name:
            payload["description"] = f"{description}\n\nOwner: {assignee_name}".strip()

        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
        }
        endpoint = f"https://www.googleapis.com/calendar/v3/calendars/{self.settings.google_calendar_id}/events"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(endpoint, headers=headers, json=payload)

        if response.is_success:
            data = response.json()
            return GoogleCalendarResult(event_id=data.get("id"), status="created")

        return GoogleCalendarResult(event_id=None, status="failed", error=response.text)

    def _build_times(self, due_date: str | None) -> tuple[datetime, datetime]:
        if due_date:
            start = datetime.fromisoformat(f"{due_date}T10:00:00+00:00")
        else:
            start = datetime.now(timezone.utc) + timedelta(days=1)
            start = start.replace(hour=10, minute=0, second=0, microsecond=0)
        end = start + timedelta(minutes=30)
        return start, end
