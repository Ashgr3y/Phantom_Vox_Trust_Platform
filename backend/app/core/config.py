from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "Phantom Vox"
    app_version: str = "1.0.0"
    environment: str = "development"
    demo_mode: bool = True
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'phantomvox.db'}"
    jwt_secret: str = "development-only-change-this-secret"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 480
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000"]
    max_upload_mb: int = 20
    retain_raw_audio: bool = False
    ephemeral_buffer_seconds: int = 15
    metadata_retention_days: int = 90
    seed_demo_data: bool = True
    demo_tick_seconds: float = 0.8
    require_ml: bool = False

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", PROJECT_ROOT / "backend" / ".env"),
        env_prefix="PHANTOM_VOX_",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("database_url")
    @classmethod
    def normalize_sqlite_url(cls, value: str) -> str:
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value.removeprefix(prefix)
        if value.startswith("sqlite:///./"):
            relative = value.removeprefix("sqlite:///./")
            return f"sqlite:///{PROJECT_ROOT / relative}"
        return value

    def validate_production(self) -> None:
        if self.environment.lower() == "production":
            if len(self.jwt_secret) < 32 or any(word in self.jwt_secret for word in ("development-only", "replace-with", "change-before")):
                raise RuntimeError("PHANTOM_VOX_JWT_SECRET must be a random secret of at least 32 characters in production")
            if not self.database_url.startswith("postgresql+psycopg://"):
                raise RuntimeError("Production requires a managed PostgreSQL PHANTOM_VOX_DATABASE_URL")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_production()
    return settings
