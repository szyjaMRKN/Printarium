#!/bin/sh
# Start kontenera backendu: migracje -> (opcjonalnie) administrator -> serwer.
set -e

echo "[ewidencja] Uruchamiam migracje bazy danych…"
python -m app.cli migrate

# Jeden proces roboczy: SQLite nie lubi wielu procesów zapisujących,
# a zadanie automatycznych kopii zapasowych ma działać dokładnie raz.
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --proxy-headers \
    --forwarded-allow-ips "*" \
    --log-level "${UVICORN_LOG_LEVEL:-info}"
