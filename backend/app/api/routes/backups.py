"""Kopie zapasowe bazy danych."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, db_session, get_current_context, require_admin
from app.core.errors import ValidationError
from app.services import backup_service

router = APIRouter(prefix="/backups", tags=["backup"])

RESTORE_CONFIRMATION = "PRZYWRACAM"


class BackupOut(BaseModel):
    filename: str
    size_bytes: int
    created_at: str
    is_automatic: bool


class RestoreRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=200)
    confirm: bool = False
    confirmation: str = Field(default="", max_length=50)


class BackupCreateRequest(BaseModel):
    note: str | None = Field(default=None, max_length=200)


def _to_out(item) -> BackupOut:
    return BackupOut(
        filename=item.filename,
        size_bytes=item.size_bytes,
        created_at=item.created_at.isoformat(),
        is_automatic=item.is_automatic,
    )


@router.get("", response_model=list[BackupOut])
def list_backups(_: CurrentUser = Depends(get_current_context)) -> list[BackupOut]:
    return [_to_out(item) for item in backup_service.list_backups()]


@router.post("", response_model=BackupOut, status_code=201)
def create_backup(
    payload: BackupCreateRequest | None = None,
    context: CurrentUser = Depends(require_admin),
    session: Session = Depends(db_session),
) -> BackupOut:
    backup = backup_service.create_backup(
        session, user=context.user, note=payload.note if payload else None, ip=context.ip
    )
    session.commit()
    return _to_out(backup)


@router.get("/export-json")
def export_json(
    _: CurrentUser = Depends(get_current_context), session: Session = Depends(db_session)
) -> Response:
    content = backup_service.export_json(session)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="eksport-danych.json"'},
    )


@router.get("/{filename}/download")
def download_backup(
    filename: str,
    _: CurrentUser = Depends(require_admin),
) -> FileResponse:
    path = backup_service.backup_path(filename)
    return FileResponse(path, media_type="application/octet-stream", filename=path.name)


@router.post("/restore")
def restore_backup(
    payload: RestoreRequest,
    context: CurrentUser = Depends(require_admin),
    session: Session = Depends(db_session),
) -> dict:
    if not payload.confirm or payload.confirmation.strip().upper() != RESTORE_CONFIRMATION:
        raise ValidationError(
            f"Przywracanie wymaga potwierdzenia. Wpisz {RESTORE_CONFIRMATION} i zaznacz zgodę."
        )
    result = backup_service.restore_backup(session, payload.filename, user=context.user, ip=context.ip)
    return {
        "message": "Baza została przywrócona z kopii zapasowej. Zaloguj się ponownie.",
        **result,
    }


@router.delete("/{filename}")
def delete_backup(
    filename: str,
    context: CurrentUser = Depends(require_admin),
    session: Session = Depends(db_session),
) -> dict:
    backup_service.delete_backup(session, filename, user=context.user, ip=context.ip)
    session.commit()
    return {"message": "Kopia zapasowa została usunięta."}
