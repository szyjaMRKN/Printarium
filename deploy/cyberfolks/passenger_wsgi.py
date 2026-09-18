"""Punkt wejścia dla Phusion Passenger (hosting współdzielony, np. cyber_Folks).

Passenger uruchamia aplikacje w standardzie WSGI, a ewidencja jest aplikacją
ASGI (FastAPI) — most robi `a2wsgi`. Serwer WSGI nie uruchamia zdarzeń
`lifespan`, dlatego migracje, dane startowe i konto administratora ze zmiennych
środowiskowych odpalamy tutaj, przy starcie procesu.

Plik leży w katalogu głównym aplikacji (Application root) obok:

    backend/    kod API
    frontend/   zbudowana aplikacja (index.html, assets/…)
    data/       baza SQLite
    backups/    kopie zapasowe
    uploads/    załączniki
    .env        konfiguracja

Automatyczne kopie zapasowe robi tu cron (`python -m app.cli auto-backup`),
a nie pętla w tle — pod Passengerem proces bywa usypiany między żądaniami.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = APP_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Bez tego ustawienia aplikacja wystartowałaby w trybie deweloperskim
# (ciasteczka bez flagi Secure, losowy SECRET_KEY przy każdym starcie).
os.environ.setdefault("APP_ENV", "production")

from app.main import app as asgi_app  # noqa: E402
from app.main import bootstrap  # noqa: E402


def _run_bootstrap() -> None:
    """Migracje pod blokadą pliku — Passenger potrafi wystartować kilka procesów."""
    lock_dir = APP_ROOT / "data"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_file = lock_dir / ".bootstrap.lock"
    try:
        import fcntl
    except ImportError:  # pragma: no cover - systemy bez fcntl
        bootstrap()
        return
    with lock_file.open("w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            bootstrap()
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


_run_bootstrap()

from a2wsgi import ASGIMiddleware  # noqa: E402

# Passenger przekazuje przedrostek adresu w SCRIPT_NAME, więc aplikacja
# działa tak samo w korzeniu domeny, jak i w podkatalogu (np. /ewidencja).
application = ASGIMiddleware(asgi_app)
