from dataclasses import dataclass

import httpx
from fastapi import UploadFile

from app.core.config import get_settings


@dataclass
class TranscriptionResult:
    transcript: str
    source: str


class TranscriptionError(RuntimeError):
    pass


class TranscriptionService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def transcribe_upload(self, upload: UploadFile) -> TranscriptionResult:
        if not upload.filename:
            raise TranscriptionError("Uploaded file is missing a filename.")

        if upload.content_type and upload.content_type.startswith("text/"):
            content = await upload.read()
            return TranscriptionResult(
                transcript=content.decode("utf-8"),
                source="manual_text_upload",
            )

        if not self.settings.whisper_base_url:
            raise TranscriptionError(
                "Whisper is not configured. Provide transcripts manually or configure WHISPER_BASE_URL."
            )

        file_content = await upload.read()
        headers = {}
        if self.settings.whisper_api_key:
            headers["Authorization"] = f"Bearer {self.settings.whisper_api_key}"

        files = {
            "file": (upload.filename, file_content, upload.content_type or "application/octet-stream"),
        }
        data = {"model": self.settings.whisper_model}

        endpoint = f"{self.settings.whisper_base_url.rstrip('/')}/audio/transcriptions"
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(endpoint, headers=headers, data=data, files=files)
            response.raise_for_status()
            payload = response.json()

        transcript = payload.get("text")
        if not transcript:
            raise TranscriptionError("Transcription provider returned no text.")

        return TranscriptionResult(transcript=transcript, source="whisper")

