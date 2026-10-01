"""Application settings, loaded from environment / .env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_db_url: str = ""
    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_live_model: str = "gemini-3.8-live"  # phone voice session; must be a Live API model
    typesafe_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
