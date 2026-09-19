"""Gemini adapter — single vision+tool-calling client (Guardian + read_imaging)."""
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import get_settings


@lru_cache
def get_llm() -> ChatGoogleGenerativeAI:
    s = get_settings()
    return ChatGoogleGenerativeAI(model=s.gemini_model, google_api_key=s.google_api_key, temperature=0)


@lru_cache
def get_advisor_llm():
    """The Advisor's chat model. Gemini by default; ADVISOR_PROVIDER=ollama runs it locally.

    Ollama is optional (`pip install -e "backend[local]"`) — a missing package raises here
    rather than at import time, so the Gemini path never depends on it.
    """
    s = get_settings()
    if s.advisor_provider.strip().lower() == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=s.ollama_model, base_url=s.ollama_base_url, temperature=0)
    return get_llm()
