from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from credential_store import get_api_key

load_dotenv()


@dataclass
class Settings:
    provider: str = os.getenv("APP_PROVIDER", "mock").lower()
    gemini_api_key: str | None = None
    gemini_backup_api_key: str | None = None
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    max_tasks: int = 4
    max_parallel_workers: int = 3
    max_revisions: int = 1
    gemini_daily_request_limit: int = int(os.getenv("GEMINI_DAILY_REQUEST_LIMIT", "20"))


settings = Settings()


def refresh_credentials() -> None:
    """Use OS-stored desktop credentials, falling back to developer .env values."""
    settings.gemini_api_key = get_api_key("primary") or os.getenv("GEMINI_API_KEY")
    settings.gemini_backup_api_key = get_api_key("backup") or os.getenv("GEMINI_BACKUP_API_KEY")


refresh_credentials()
