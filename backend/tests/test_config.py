from app.config import get_settings


def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://x")
    monkeypatch.setenv("GOOGLE_API_KEY", "k")
    monkeypatch.setenv("TYPESAFE_API_KEY", "t")
    get_settings.cache_clear()
    s = get_settings()
    assert s.supabase_db_url == "postgresql://x"
    assert s.gemini_model == "gemini-2.5-flash"  # default
