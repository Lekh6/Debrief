import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

import httpx
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import GoogleOAuthCredential


@dataclass
class GoogleCalendarResult:
    event_id: str | None
    status: str
    error: str | None = None


class GoogleCalendarService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def create_event(
        self,
        db: Session,
        project_id: UUID | str,
        title: str,
        description: str,
        due_date: str | None,
        assignee_name: str | None,
        assignee_email: str | None,
    ) -> GoogleCalendarResult:
        access_token = await self._get_google_access_token(db=db, project_id=project_id)
        if not access_token or not self.settings.google_calendar_id:
            return GoogleCalendarResult(
                event_id=None,
                status="not_configured",
                error="Google Calendar OAuth is not connected for this project.",
            )

        payload = {
            "summary": title,
            "description": description,
        }
        if due_date:
            payload["start"] = {"date": due_date}
            payload["end"] = {"date": self._next_day_iso(due_date)}
        else:
            event_start, event_end = self._build_times(due_date)
            payload["start"] = {"dateTime": event_start.isoformat()}
            payload["end"] = {"dateTime": event_end.isoformat()}

        if assignee_name:
            payload["description"] = f"{description}\n\nOwner: {assignee_name}".strip()
        if assignee_email:
            payload["attendees"] = [{"email": assignee_email}]

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        endpoint = f"https://www.googleapis.com/calendar/v3/calendars/{self.settings.google_calendar_id}/events"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    params={"sendUpdates": "all"},
                )
        except Exception as exc:
            return GoogleCalendarResult(event_id=None, status="failed", error=str(exc))

        if response.is_success:
            data = response.json()
            return GoogleCalendarResult(event_id=data.get("id"), status="created")

        if response.status_code == 401:
            await self._delete_project_credential(db=db, project_id=project_id)
            return GoogleCalendarResult(
                event_id=None,
                status="needs_reconnect",
                error="Google Calendar authorization expired or was revoked. Reconnect Google Calendar for this project and try again.",
            )

        if assignee_email and "forbiddenForServiceAccounts" in response.text:
            payload.pop("attendees", None)
            payload["description"] = (
                f"{payload.get('description', '').strip()}\n\nAssignee email recorded: {assignee_email}"
            ).strip()
            async with httpx.AsyncClient(timeout=30) as client:
                fallback_response = await client.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    params={"sendUpdates": "none"},
                )
            if fallback_response.is_success:
                data = fallback_response.json()
                return GoogleCalendarResult(
                    event_id=data.get("id"),
                    status="created_without_attendee",
                    error="Event created, but attendee invite was skipped because service accounts cannot invite attendees without domain-wide delegation.",
                )

        return GoogleCalendarResult(event_id=None, status="failed", error=response.text)

    def _build_times(self, due_date: str | None) -> tuple[datetime, datetime]:
        if due_date:
            start = datetime.fromisoformat(f"{due_date}T10:00:00+00:00")
        else:
            start = datetime.now(timezone.utc) + timedelta(days=1)
            start = start.replace(hour=10, minute=0, second=0, microsecond=0)
        end = start + timedelta(minutes=30)
        return start, end

    def _next_day_iso(self, due_date: str) -> str:
        current = date.fromisoformat(due_date)
        return (current + timedelta(days=1)).isoformat()

    async def _get_google_access_token(self, db: Session, project_id: UUID | str) -> str | None:
        if isinstance(project_id, str):
            try:
                project_id = UUID(project_id)
            except ValueError:
                return None

        credential = (
            db.query(GoogleOAuthCredential)
            .filter(GoogleOAuthCredential.project_id == project_id)
            .one_or_none()
        )
        if credential is None:
            if not self.settings.google_service_account_json:
                return None
            credentials = service_account.Credentials.from_service_account_info(
                json.loads(self.settings.google_service_account_json),
                scopes=["https://www.googleapis.com/auth/calendar"],
            )
            credentials.refresh(Request())
            return credentials.token

        expires_at = credential.expires_at.replace(tzinfo=timezone.utc) if credential.expires_at else None
        if expires_at and expires_at > datetime.now(timezone.utc) + timedelta(minutes=2):
            return credential.access_token

        if not credential.refresh_token or not self.settings.google_oauth_client_id or not self.settings.google_oauth_client_secret:
            return None

        async with httpx.AsyncClient(timeout=30) as client:
            token_response = await client.post(
                credential.token_uri,
                data={
                    "client_id": self.settings.google_oauth_client_id,
                    "client_secret": self.settings.google_oauth_client_secret,
                    "refresh_token": credential.refresh_token,
                    "grant_type": "refresh_token",
                },
            )
        if not token_response.is_success:
            db.delete(credential)
            db.commit()
            return None

        payload = token_response.json()
        credential.access_token = payload["access_token"]
        credential.expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=payload.get("expires_in", 3600))
        ).replace(tzinfo=None)
        db.commit()
        return credential.access_token

    async def _delete_project_credential(self, db: Session, project_id: UUID | str) -> None:
        if isinstance(project_id, str):
            try:
                project_id = UUID(project_id)
            except ValueError:
                return
        credential = (
            db.query(GoogleOAuthCredential)
            .filter(GoogleOAuthCredential.project_id == project_id)
            .one_or_none()
        )
        if credential is not None:
            db.delete(credential)
            db.commit()
