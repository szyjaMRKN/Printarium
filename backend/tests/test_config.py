"""Konfiguracja ze zmiennych środowiskowych."""

from __future__ import annotations

import pytest

from app.core.config import Settings, get_settings


def test_puste_wartosci_w_env_sa_ignorowane(monkeypatch):
    # Plik .env z produkcji zawiera wpisy w rodzaju `COOKIE_SECURE=` — nie mogą
    # wywracać startu aplikacji.
    monkeypatch.setenv("COOKIE_SECURE", "")
    monkeypatch.setenv("COOKIE_DOMAIN", "")
    monkeypatch.setenv("CORS_ORIGINS", "")
    monkeypatch.setenv("SECRET_KEY", "klucz-testowy")
    monkeypatch.setenv("APP_ENV", "production")
    get_settings.cache_clear()

    settings = Settings()
    assert settings.cookie_secure is None
    assert settings.cookie_domain is None
    assert settings.cors_origins == []
    # W produkcji ciasteczka zawsze lecą z flagą Secure.
    assert settings.cookies_secure is True
    get_settings.cache_clear()


def test_lista_origins_z_przecinkow(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://a.example.com, https://b.example.com")
    monkeypatch.setenv("SECRET_KEY", "klucz-testowy")
    get_settings.cache_clear()
    assert Settings().cors_origins == ["https://a.example.com", "https://b.example.com"]
    get_settings.cache_clear()


def test_produkcja_wymaga_secret_key(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "")
    get_settings.cache_clear()
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        get_settings()
    get_settings.cache_clear()


def test_sciezka_bazy_jest_w_katalogu_danych(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "dane"))
    monkeypatch.setenv("SECRET_KEY", "klucz-testowy")
    get_settings.cache_clear()
    settings = Settings()
    assert settings.db_path == tmp_path / "dane" / "database.sqlite3"
    assert settings.sqlalchemy_url.startswith("sqlite+pysqlite:///")
    get_settings.cache_clear()
