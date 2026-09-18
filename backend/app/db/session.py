"""Silnik SQLAlchemy, pragmy SQLite i sesje.

Warstwa danych jest napisana tak, aby przejście na PostgreSQL wymagało zmiany
wyłącznie adresu bazy: pragmy ustawiamy tylko dla dialektu sqlite, a logika
biznesowa nie korzysta z funkcji specyficznych dla SQLite.
"""

from __future__ import annotations

from collections.abc import Generator, Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def _configure_sqlite(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=10000")
    cursor.close()


def build_engine(url: str | None = None) -> Engine:
    settings = get_settings()
    url = url or settings.sqlalchemy_url
    is_sqlite = url.startswith("sqlite")
    if is_sqlite and ":memory:" not in url:
        db_file = url.split("///", 1)[-1]
        Path(db_file).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        url,
        future=True,
        echo=settings.app_debug,
        connect_args={"check_same_thread": False} if is_sqlite else {},
        pool_pre_ping=True,
    )
    if is_sqlite:
        event.listen(engine, "connect", _configure_sqlite)
    return engine


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = build_engine()
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)
    return _session_factory


def reset_engine() -> None:
    """Używane w testach i po zmianie pliku bazy (przywracanie backupu)."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


@contextmanager
def session_scope() -> Iterator[Session]:
    """Krótka transakcja zapisu — commit albo rollback, zawsze zamknięcie."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """Zależność FastAPI."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
