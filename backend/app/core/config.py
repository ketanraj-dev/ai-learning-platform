"""
app/core/config.py
------------------
Reads your .env file and exposes every setting as a typed Python attribute.

HOW IT WORKS:
  - pydantic-settings reads .env automatically
  - @lru_cache means .env is read ONCE, not on every request
  - Every other file does:  from app.core.config import get_settings
                            settings = get_settings()
                            print(settings.openai_api_key)

ADD NEW SETTINGS:
  1. Add the key=value line to your .env file
  2. Add a matching typed field below
  That's it — available everywhere instantly.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── App ────────────────────────────────────────────────────
    app_name: str = "AI Learning Platform"
    debug: bool = False

    # ── JWT / Auth ─────────────────────────────────────────────
    # Change SECRET_KEY in .env to any long random string in production
    secret_key: str = "change-this-to-a-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60       # 1 hour
    refresh_token_expire_days: int = 7          # 1 week

    # ── Database ───────────────────────────────────────────────
    # Default: SQLite (zero setup, single file in backend/ folder)
    # To use PostgreSQL later, just change this line in .env:
    #   DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname
    database_url: str = "sqlite+aiosqlite:///./learning_platform.db"

    # ── OpenAI ─────────────────────────────────────────────────
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"          # affordable model

    # ── CORS ───────────────────────────────────────────────────
    # This tells FastAPI which frontend URL is allowed to call the API
    frontend_url: str = "http://localhost:5173"  # Vite default port

    # ── pydantic-settings config ───────────────────────────────
    model_config = SettingsConfigDict(
        env_file=".env",            # file to read
        env_file_encoding="utf-8",  # encoding
        case_sensitive=False,       # DATABASE_URL == database_url
        extra="ignore",             # ignore unknown keys in .env
    )


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    The @lru_cache decorator means this function runs ONCE
    and returns the same object on every subsequent call.
    This prevents reading the .env file on every API request.
    """
    return Settings()