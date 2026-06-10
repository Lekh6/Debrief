import asyncio
import os
import tempfile
from datetime import datetime, timezone
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

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

        file_content = await upload.read()
        transcript = await asyncio.to_thread(self._transcribe_with_faster_whisper, upload.filename, file_content)
        if not transcript:
            raise TranscriptionError("faster-whisper returned no text.")

        return TranscriptionResult(transcript=transcript, source="faster_whisper")

    def _transcribe_with_faster_whisper(self, filename: str, file_content: bytes) -> str:
        model = _get_faster_whisper_model(
            self.settings.faster_whisper_model,
            self.settings.faster_whisper_device,
            self.settings.faster_whisper_compute_type,
        )
        suffix = os.path.splitext(filename)[1] or ".wav"
        self._persist_recording(filename=filename, file_content=file_content, suffix=suffix)
        temp_path = ""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(file_content)
                temp_path = temp_file.name
            segments, _info = model.transcribe(
                temp_path,
                language=self.settings.faster_whisper_language or None,
                beam_size=max(self.settings.faster_whisper_beam_size, 1),
                vad_filter=self.settings.faster_whisper_vad_filter,
            )
            return " ".join(segment.text.strip() for segment in segments if segment.text and segment.text.strip()).strip()
        except ImportError as exc:
            raise TranscriptionError(
                "faster-whisper is not installed. Install with `pip install faster-whisper` and ensure ffmpeg is available."
            ) from exc
        except Exception as exc:
            raise TranscriptionError(f"faster-whisper transcription failed: {exc}") from exc
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    def _persist_recording(self, filename: str, file_content: bytes, suffix: str) -> None:
        root_dir = Path(__file__).resolve().parents[4]
        recordings_dir = root_dir / "recordings"
        recordings_dir.mkdir(parents=True, exist_ok=True)

        file_stem = Path(filename).stem.strip() or "recording"
        safe_stem = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in file_stem)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        artifact_name = f"{safe_stem}-{timestamp}-{uuid4().hex[:8]}{suffix}"
        (recordings_dir / artifact_name).write_bytes(file_content)


@lru_cache(maxsize=1)
def _get_faster_whisper_model(model_name: str, device: str, compute_type: str):
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise ImportError("faster-whisper import failed.") from exc
    try:
        return WhisperModel(model_name, device=device, compute_type=compute_type)
    except Exception as exc:
        # Common on Windows without CUDA runtime: cublas64_12.dll missing.
        # Fall back to CPU so local demos keep working without GPU setup.
        lowered = str(exc).lower()
        requested_device = (device or "").lower()
        if requested_device != "cpu" and ("cublas" in lowered or "cuda" in lowered):
            return WhisperModel(model_name, device="cpu", compute_type="int8")
        raise
