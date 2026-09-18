"""Health check — bez danych wrażliwych."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.core.version import APP_VERSION

router = APIRouter(tags=["system"])


@router.get("/health")
def health(session: Session = Depends(db_session)) -> dict:
    database_ok = True
    try:
        session.execute(text("SELECT 1"))
    except Exception:  # pragma: no cover - awaria bazy
        database_ok = False
    return {
        "status": "ok" if database_ok else "degraded",
        "database": "ok" if database_ok else "error",
        "version": APP_VERSION,
    }
