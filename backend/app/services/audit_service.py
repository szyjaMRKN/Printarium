"""Dziennik zmian. Nigdy nie zapisujemy tu haseł, tokenów ani sekretów."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.core.dates import utcnow
from app.models.audit import AuditLog
from app.models.user import User

SENSITIVE_KEYS = {"password", "haslo", "password_hash", "token", "secret", "csrf"}


def _sanitize(meta: dict[str, Any] | None) -> dict[str, Any] | None:
    if not meta:
        return None
    return {key: value for key, value in meta.items() if key.lower() not in SENSITIVE_KEYS}


def record(
    session: Session,
    action: str,
    *,
    user: User | None = None,
    user_login: str | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    description: str | None = None,
    ip_address: str | None = None,
    meta: dict[str, Any] | None = None,
) -> AuditLog:
    entry = AuditLog(
        created_at=utcnow(),
        user_id=user.id if user else None,
        user_login=user.login if user else user_login,
        action=str(action),
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        ip_address=ip_address,
        meta=_sanitize(meta),
    )
    session.add(entry)
    session.flush()
    return entry


def query(
    *,
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    user_id: int | None = None,
) -> Select[tuple[AuditLog]]:
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id is not None:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if user_id is not None:
        stmt = stmt.where(AuditLog.user_id == user_id)
    return stmt
