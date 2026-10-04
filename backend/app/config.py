"""Application settings, loaded from environment / .env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", protected_namespaces=("settings_",))

    app_name: str = "smallai-backend"
    debug: bool = True
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Guardrail: below this the tool must defer to a human instead of guessing.
    confidence_threshold: float = 0.65

    # Local language used in the demo (ISO 639-1). Hindi.
    default_language: str = "hi"

    model_dir: str = "./models"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
