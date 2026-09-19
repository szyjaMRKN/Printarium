"""Migracje muszą ruszyć także tam, gdzie system ma lokalizację ASCII.

Na hostingu współdzielonym proces aplikacji startuje z lokalizacją POSIX,
a Alembic (i `logging.config.fileConfig`) czytają `alembic.ini` w kodowaniu
lokalizacji. Jeden znak spoza ASCII w tym pliku wywracał tam start aplikacji
błędem UnicodeDecodeError — stąd ten test.
"""

from __future__ import annotations

from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]


def test_alembic_ini_jest_czystym_ascii() -> None:
    dane = (BACKEND_DIR / "alembic.ini").read_bytes()
    podejrzane = [(numer, bajt) for numer, bajt in enumerate(dane) if bajt > 127]
    assert not podejrzane, (
        "alembic.ini zawiera znaki spoza ASCII na pozycjach %s — na hostingu "
        "z lokalizacją ASCII to zatrzyma migracje przy starcie." % (podejrzane[:5],)
    )


def test_migracje_dzialaja_w_lokalizacji_ascii(tmp_path, monkeypatch) -> None:
    """Pełne `alembic upgrade head` z odczytem konfiguracji jak na hostingu."""
    import configparser

    from app.core.config import get_settings
    from app.db.session import reset_engine
    from app.services.backup_service import run_migrations

    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("BACKUP_DIR", str(tmp_path / "backups"))
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("DATABASE_URL", "")
    get_settings.cache_clear()
    reset_engine()
    get_settings().ensure_directories()

    # Odtworzenie zachowania serwera: konfiguracja czytana w ASCII.
    oryginalny_read = configparser.RawConfigParser.read

    def read_w_ascii(self, filenames, encoding=None):
        return oryginalny_read(self, filenames, encoding="ascii")

    monkeypatch.setattr(configparser.RawConfigParser, "read", read_w_ascii)

    run_migrations()

    reset_engine()
    get_settings.cache_clear()
    assert (tmp_path / "data" / "database.sqlite3").exists()
