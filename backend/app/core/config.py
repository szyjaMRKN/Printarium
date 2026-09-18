"""Konfiguracja aplikacji pobierana ze zmiennych środowiskowych.

Żadnych sekretów w kodzie — wszystko przychodzi z env (plik .env w developmencie,
zmienne kontenera w produkcji). Wartości prawne/podatkowe nie znajdują się tutaj,
tylko w bazie (tabela ustawień i lat podatkowych), żeby dało się je zmienić z UI.
"""

from __future__ import annotations

import secrets
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BASE_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_DIR / ".env", BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- środowisko ---
    app_env: Literal["development", "test", "production"] = "development"
    app_debug: bool = False
    secret_key: str = ""
    timezone: str = "Europe/Warsaw"

    # --- katalogi danych (nigdy w katalogu publicznym serwera WWW) ---
    data_dir: Path = REPO_DIR / "data"
    backup_dir: Path = REPO_DIR / "backups"
    upload_dir: Path = REPO_DIR / "uploads"
    database_url: str = ""

    # Katalog ze zbudowanym frontendem. Puste = backend wystawia samo API
    # (tak działa wariant z Dockerem, gdzie pliki statyczne serwuje Caddy).
    # Ustawiany na hostingu współdzielonym, gdzie nie ma osobnego serwera statycznego.
    frontend_dir: Path | None = None

    # --- sesje i ciasteczka ---
    session_cookie_name: str = "ewid_session"
    csrf_cookie_name: str = "ewid_csrf"
    csrf_header_name: str = "X-CSRF-Token"
    cookie_secure: bool | None = None  # None => automatycznie: produkcja = True
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cookie_domain: str | None = None
    session_idle_minutes: int = 720
    session_absolute_hours: int = 168

    # --- ochrona logowania ---
    login_max_attempts: int = 5
    login_window_minutes: int = 15
    login_lock_minutes: int = 15

    # --- API / dokumentacja ---
    enable_docs: bool = True
    # NoDecode: wartość z .env jest listą rozdzieloną przecinkami, nie JSON-em.
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    api_prefix: str = "/api"

    # --- pliki ---
    max_upload_mb: int = 10

    # --- bootstrap administratora (tylko pierwsze uruchomienie) ---
    admin_login: str = ""
    admin_password: str = ""
    admin_email: str = ""

    # --- backup ---
    backup_retention: int = 30
    backup_auto_enabled: bool = True
    backup_auto_hour: int = 3
    backup_auto_minute: int = 0

    # --- PDF ---
    pdf_font_path: str = ""

    @model_validator(mode="before")
    @classmethod
    def _ignore_empty_values(cls, values: object) -> object:
        """Puste wpisy w .env (np. `COOKIE_SECURE=`) traktujemy jak brak wartości."""
        if isinstance(values, dict):
            return {
                key: value
                for key, value in values.items()
                if key.lower() == "cors_origins" or not (isinstance(value, str) and value.strip() == "")
            }
        return values

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value or []

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def cookies_secure(self) -> bool:
        if self.cookie_secure is None:
            return self.is_production
        return self.cookie_secure

    @property
    def db_path(self) -> Path:
        return self.data_dir / "database.sqlite3"

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"sqlite+pysqlite:///{self.db_path}"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def frontend_path(self) -> Path | None:
        """Katalog z plikami frontendu — tylko jeśli faktycznie istnieje.

        Ścieżkę względną liczymy od katalogu projektu, żeby w pliku `.env`
        wystarczyło `FRONTEND_DIR=frontend`.
        """
        if self.frontend_dir is None:
            return None
        directory = self.frontend_dir
        if not directory.is_absolute():
            directory = REPO_DIR / directory
        directory = directory.resolve()
        return directory if (directory / "index.html").is_file() else None

    def ensure_directories(self) -> None:
        for directory in (self.data_dir, self.backup_dir, self.upload_dir):
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.secret_key:
        if settings.is_production:
            raise RuntimeError(
                "Brak SECRET_KEY. Ustaw zmienną środowiskową SECRET_KEY przed uruchomieniem produkcyjnym."
            )
        # W developmencie klucz jest generowany losowo przy starcie procesu.
        settings.secret_key = secrets.token_urlsafe(48)
    return settings
