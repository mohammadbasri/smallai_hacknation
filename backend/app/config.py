"""Application settings, loaded from environment / .env."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", protected_namespaces=("settings_",))

    app_name: str = "karibu-backend"
    debug: bool = True
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Guardrail: below this the tool must defer to a human instead of guessing.
    confidence_threshold: float = 0.65

    # Operator's language (ISO 639-1). The demo language is Swahili; visitors are answered in en/fr/sw.
    default_language: str = "sw"

    # Shared artifacts (models + reply templates) read by both runtimes. Default: <repo>/shared
    shared_dir: str = str(REPO_DIR / "shared")

    # SQLite file for sync records, enquiries, bookings, feedback, profile, SMS outbox.
    db_path: str = str(BACKEND_DIR / "data" / "karibu.db")

    # Built frontend to serve from the same origin (single-container deployment). Empty = API only.
    static_dir: str = str(REPO_DIR / "frontend" / "dist")

    # SMS channel. "console" stores outgoing messages in the outbox only (demo / tests).
    # "africastalking" or "twilio" send for real when credentials are set.
    sms_provider: str = "console"
    sms_operator_number: str = "+000000000000"  # Noor's basic phone
    sms_service_number: str = "+000000000001"  # the number visitors text
    at_username: str = ""
    at_api_key: str = ""
    at_sender_id: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def shared_path(self) -> Path:
        return Path(self.shared_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()
