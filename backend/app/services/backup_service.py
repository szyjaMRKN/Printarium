"""Kopie zapasowe bazy SQLite.

Kopię robimy wyłącznie przez SQLite Backup API (sqlite3.Connection.backup),
nigdy zwykłym kopiowaniem aktywnego pliku — to jedyny sposób na spójną kopię
przy włączonym trybie WAL.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dates import WARSAW, utcnow
from app.core.errors import NotFoundError, ValidationError
from app.db.base import Base
from app.db.session import get_engine, reset_engine
from app.models.enums import AuditAction
from app.models.user import User
from app.services import audit_service
from app.services.settings_service import SettingsService

BACKUP_PREFIX = "backup_"
BACKUP_SUFFIX = ".sqlite3"
REQUIRED_TABLES = {"sales", "payments", "costs", "users", "alembic_version"}


@dataclass
class BackupFile:
    filename: str
    size_bytes: int
    created_at: datetime

    @property
    def is_automatic(self) -> bool:
        return "_auto" in self.filename


def backup_dir() -> Path:
    directory = get_settings().backup_dir
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def database_path() -> Path:
    settings = get_settings()
    url = settings.sqlalchemy_url
    if not url.startswith("sqlite"):
        raise ValidationError("Kopie zapasowe w tej wersji obsługują wyłącznie bazę SQLite.")
    return Path(url.split("///", 1)[-1])


def _safe_backup_path(filename: str) -> Path:
    name = Path(filename).name
    if not name.startswith(BACKUP_PREFIX) or not name.endswith(BACKUP_SUFFIX):
        raise ValidationError("Nieprawidłowa nazwa pliku kopii zapasowej.")
    path = (backup_dir() / name).resolve()
    if path.parent != backup_dir().resolve():
        raise ValidationError("Nieprawidłowa ścieżka pliku kopii zapasowej.")
    return path


def list_backups() -> list[BackupFile]:
    items: list[BackupFile] = []
    for path in backup_dir().glob(f"{BACKUP_PREFIX}*{BACKUP_SUFFIX}"):
        stat = path.stat()
        items.append(
            BackupFile(
                filename=path.name,
                size_bytes=stat.st_size,
                created_at=datetime.fromtimestamp(stat.st_mtime, tz=WARSAW),
            )
        )
    return sorted(items, key=lambda item: item.created_at, reverse=True)


def _timestamp_name(suffix: str = "") -> str:
    stamp = datetime.now(tz=WARSAW).strftime("%Y-%m-%d_%H-%M-%S")
    return f"{BACKUP_PREFIX}{stamp}{suffix}{BACKUP_SUFFIX}"


def create_backup(
    session: Session | None = None,
    *,
    user: User | None = None,
    automatic: bool = False,
    note: str | None = None,
    ip: str | None = None,
) -> BackupFile:
    source = database_path()
    if not source.exists():
        raise NotFoundError("Plik bazy danych nie istnieje.")

    target = backup_dir() / _timestamp_name("_auto" if automatic else "")
    source_connection = sqlite3.connect(str(source))
    target_connection = sqlite3.connect(str(target))
    try:
        with target_connection:
            source_connection.backup(target_connection)
    finally:
        target_connection.close()
        source_connection.close()

    stat = target.stat()
    backup = BackupFile(
        filename=target.name,
        size_bytes=stat.st_size,
        created_at=datetime.fromtimestamp(stat.st_mtime, tz=WARSAW),
    )
    if session is not None:
        audit_service.record(
            session,
            AuditAction.BACKUP_CREATE,
            user=user,
            entity_type="backup",
            ip_address=ip,
            description=f"Utworzono kopię zapasową {backup.filename}"
            + (f" ({note})" if note else "")
            + (" [automatyczna]" if automatic else ""),
        )
        cleanup_old_backups(SettingsService(session).get_int("backup.retention"))
    return backup


def cleanup_old_backups(retention: int) -> list[str]:
    """Zostawia N najnowszych kopii, starsze usuwa."""
    if retention <= 0:
        return []
    removed: list[str] = []
    for backup in list_backups()[retention:]:
        path = backup_dir() / backup.filename
        path.unlink(missing_ok=True)
        removed.append(backup.filename)
    return removed


def verify_backup_file(path: Path) -> None:
    """Sprawdza integralność pliku kopii przed przywróceniem."""
    if not path.exists():
        raise NotFoundError("Nie znaleziono pliku kopii zapasowej.")
    connection = None
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        result = connection.execute("PRAGMA integrity_check").fetchone()
        if not result or result[0] != "ok":
            raise ValidationError("Kopia zapasowa jest uszkodzona (integrity_check nie powiódł się).")
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    except sqlite3.Error as exc:
        raise ValidationError(f"Plik nie jest poprawną bazą SQLite: {exc}") from exc
    finally:
        if connection is not None:
            connection.close()

    missing = REQUIRED_TABLES - tables
    if missing:
        raise ValidationError(
            "Plik nie wygląda na kopię tej aplikacji. Brakuje tabel: " + ", ".join(sorted(missing)) + "."
        )


def restore_backup(
    session: Session, filename: str, *, user: User | None = None, ip: str | None = None
) -> dict:
    """Przywraca bazę: weryfikacja -> kopia bezpieczeństwa -> podmiana -> migracje."""
    path = _safe_backup_path(filename)
    verify_backup_file(path)

    safety_copy = create_backup(session, user=user, automatic=True, note="kopia sprzed przywrócenia", ip=ip)
    session.commit()

    target = database_path()
    reset_engine()
    for suffix in ("-wal", "-shm"):
        Path(str(target) + suffix).unlink(missing_ok=True)
    shutil.copy2(path, target)

    run_migrations()
    reset_engine()

    from app.db.session import session_scope

    with session_scope() as fresh_session:
        audit_service.record(
            fresh_session,
            AuditAction.BACKUP_RESTORE,
            user=user,
            entity_type="backup",
            ip_address=ip,
            description=f"Przywrócono bazę z kopii {filename}. Kopia bezpieczeństwa: {safety_copy.filename}.",
        )
    return {"restored_from": filename, "safety_backup": safety_copy.filename}


def delete_backup(session: Session, filename: str, *, user: User | None = None, ip: str | None = None) -> None:
    path = _safe_backup_path(filename)
    if not path.exists():
        raise NotFoundError("Nie znaleziono pliku kopii zapasowej.")
    path.unlink()
    audit_service.record(
        session,
        AuditAction.BACKUP_DELETE,
        user=user,
        entity_type="backup",
        ip_address=ip,
        description=f"Usunięto kopię zapasową {filename}.",
    )


def backup_path(filename: str) -> Path:
    path = _safe_backup_path(filename)
    if not path.exists():
        raise NotFoundError("Nie znaleziono pliku kopii zapasowej.")
    return path


def run_migrations() -> None:
    """Uruchamia `alembic upgrade head` w tym samym procesie."""
    from alembic import command
    from alembic.config import Config

    config_path = Path(__file__).resolve().parents[2] / "alembic.ini"
    config = Config(str(config_path))
    config.set_main_option("script_location", str(config_path.parent / "alembic"))
    command.upgrade(config, "head")


def export_json(session: Session) -> bytes:
    """Pełny eksport danych do JSON (czytelny, niezależny od SQLite)."""
    engine = get_engine()
    inspector = inspect(engine)
    payload: dict[str, list[dict]] = {}
    for table_name in sorted(Base.metadata.tables):
        if table_name not in inspector.get_table_names():
            continue
        table = Base.metadata.tables[table_name]
        rows = session.execute(select(table)).mappings().all()
        payload[table_name] = [
            {key: _json_value(value) for key, value in dict(row).items()} for row in rows
        ]
    document = {
        "exported_at": utcnow().isoformat(),
        "tables": payload,
    }
    return json.dumps(document, ensure_ascii=False, indent=2).encode("utf-8")


def _json_value(value):
    if isinstance(value, (datetime,)):
        return value.isoformat()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, bytes):  # pragma: no cover - brak kolumn binarnych
        return value.decode("utf-8", "replace")
    return value


def due_for_automatic_backup(session: Session, now: datetime | None = None) -> bool:
    settings_service = SettingsService(session)
    if not settings_service.get_bool("backup.auto_enabled"):
        return False
    now = now or datetime.now(tz=WARSAW)
    scheduled = now.replace(
        hour=settings_service.get_int("backup.auto_hour"),
        minute=settings_service.get_int("backup.auto_minute"),
        second=0,
        microsecond=0,
    )
    if now < scheduled:
        return False
    for backup in list_backups():
        if backup.is_automatic and backup.created_at >= scheduled:
            return False
    return True
