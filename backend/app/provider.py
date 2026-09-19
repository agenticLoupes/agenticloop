"""Gemini adapter — single vision+tool-calling client (Guardian + read_imaging)."""
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import get_settings


@lru_cache
def get_llm() -> ChatGoogleGenerativeAI:
    s = get_settings()
    return ChatGoogleGenerativeAI(model=s.gemini_model, google_api_key=s.google_api_key, temperature=0)
