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

    # Advisor model. "gemini" reuses the Guardian's client; "ollama" runs it locally
    # (langchain-ollama, installed with the `local` extra) for offline development.
    advisor_provider: str = "gemini"
    ollama_model: str = "llama3.2:3b"
    ollama_base_url: str = "http://localhost:11434"


@lru_cache
def get_settings() -> Settings:
    return Settings()
