from functools import lru_cache
import json

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "Post-Meeting Task Automation API"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./meetings.db"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    sql_echo: bool = False

    faster_whisper_model: str = "small"
    faster_whisper_device: str = "auto"
    faster_whisper_compute_type: str = "int8"
    faster_whisper_language: str | None = None
    faster_whisper_beam_size: int = 5
    faster_whisper_vad_filter: bool = True

    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    use_heuristic_extractor: bool = True

    auto_create_jira_on_confirm: bool = False
    auto_create_google_calendar_on_confirm: bool = False
    auto_notify_slack_on_confirm: bool = False

    jira_base_url: str | None = None
    jira_user_email: str | None = None
    jira_api_token: str | None = None

    slack_bot_token: str | None = None

    google_calendar_id: str | None = None
    google_service_account_json: str | None = None
    google_oauth_client_id: str | None = None
    google_oauth_client_secret: str | None = None
    google_oauth_redirect_uri: str | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                return json.loads(stripped)
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
