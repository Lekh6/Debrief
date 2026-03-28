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

    whisper_base_url: str | None = None
    whisper_api_key: str | None = None
    whisper_model: str = "whisper-1"

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

    google_calendar_id: str | None = None
    google_service_account_json: str | None = None

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
