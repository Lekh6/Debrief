from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.entities import GoogleOAuthCredential, Project


router = APIRouter(prefix="/auth/google", tags=["google-auth"])


@router.get("/start")
def start_google_oauth(project_id: UUID, db: Session = Depends(get_db)) -> RedirectResponse:
    settings = get_settings()
    project = db.query(Project).filter(Project.project_id == project_id).one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if not settings.google_oauth_client_id or not settings.google_oauth_redirect_uri:
        raise HTTPException(status_code=400, detail="Google OAuth is not configured.")

    query = urlencode(
        {
            "client_id": settings.google_oauth_client_id,
            "redirect_uri": settings.google_oauth_redirect_uri,
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent",
            "scope": "openid email profile https://www.googleapis.com/auth/calendar.events",
            "state": str(project_id),
        }
    )
    return RedirectResponse(url=f"https://accounts.google.com/o/oauth2/v2/auth?{query}")


@router.get("/callback")
async def google_oauth_callback(code: str, state: str, db: Session = Depends(get_db)) -> HTMLResponse:
    settings = get_settings()
    if not settings.google_oauth_client_id or not settings.google_oauth_client_secret or not settings.google_oauth_redirect_uri:
        raise HTTPException(status_code=400, detail="Google OAuth is not configured.")

    project = db.query(Project).filter(Project.project_id == state).one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found for OAuth callback.")

    async with httpx.AsyncClient(timeout=30) as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "redirect_uri": settings.google_oauth_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
    if not token_response.is_success:
        raise HTTPException(status_code=400, detail=token_response.text)

    token_payload = token_response.json()
    google_email = await _fetch_google_email(token_payload["access_token"])
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_payload.get("expires_in", 3600))

    credential = (
        db.query(GoogleOAuthCredential)
        .filter(GoogleOAuthCredential.project_id == project.project_id)
        .one_or_none()
    )
    if credential is None:
        credential = GoogleOAuthCredential(
            project_id=project.project_id,
            access_token=token_payload["access_token"],
            refresh_token=token_payload.get("refresh_token"),
            google_email=google_email,
            token_uri="https://oauth2.googleapis.com/token",
            scope=token_payload.get("scope"),
            expires_at=expires_at.replace(tzinfo=None),
        )
        db.add(credential)
    else:
        credential.access_token = token_payload["access_token"]
        credential.refresh_token = token_payload.get("refresh_token") or credential.refresh_token
        credential.google_email = google_email
        credential.scope = token_payload.get("scope")
        credential.expires_at = expires_at.replace(tzinfo=None)

    db.commit()

    return HTMLResponse(
        "<html><body style='font-family:sans-serif;padding:24px;'>"
        "<h2>Google Calendar connected</h2>"
        "<p>You can close this tab and return to Debrief.</p>"
        f"<p>Connected account: <strong>{google_email}</strong></p>"
        f"<p>Project: <strong>{project.name}</strong></p>"
        "</body></html>"
    )


@router.get("/status")
def google_oauth_status(project_id: UUID, db: Session = Depends(get_db)) -> dict[str, str | bool | None]:
    credential = (
        db.query(GoogleOAuthCredential)
        .filter(GoogleOAuthCredential.project_id == project_id)
        .one_or_none()
    )
    return {
        "connected": credential is not None,
        "google_email": credential.google_email if credential else None,
    }


async def _fetch_google_email(access_token: str) -> str | None:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if not response.is_success:
        return None
    return response.json().get("email")
