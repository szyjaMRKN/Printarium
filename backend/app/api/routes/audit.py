"""Dziennik zmian."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, db_session, get_current_context
from app.repositories.base import paginate
from app.schemas.common import PageMeta, PageResponse
from app.services import audit_service

router = APIRouter(prefix="/audit-logs", tags=["dziennik"])


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    user_login: str | None
    action: str
    entity_type: str | None
    entity_id: int | None
    description: str | None
    ip_address: str | None


@router.get("", response_model=PageResponse[AuditLogOut])
def list_audit_logs(
    action: str | None = Query(default=None, max_length=64),
    entity_type: str | None = Query(default=None, max_length=64),
    entity_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    _: CurrentUser = Depends(get_current_context),
    session: Session = Depends(db_session),
) -> PageResponse[AuditLogOut]:
    stmt = audit_service.query(action=action, entity_type=entity_type, entity_id=entity_id)
    result = paginate(session, stmt, page, per_page)
    return PageResponse[AuditLogOut](
        items=[AuditLogOut.model_validate(item) for item in result.items],
        meta=PageMeta(total=result.total, page=result.page, per_page=result.per_page, pages=result.pages),
    )
