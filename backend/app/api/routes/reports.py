"""Raporty i eksporty (CSV / XLSX / PDF) generowane po stronie serwera."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, db_session, get_current_context
from app.core.errors import ValidationError
from app.services import export_service, reports_service

router = APIRouter(prefix="/reports", tags=["raporty"])


@router.get("")
def available_reports(_: CurrentUser = Depends(get_current_context)) -> list[dict]:
    return [{"key": key, "title": title} for key, title in reports_service.AVAILABLE_REPORTS]


def _build(
    session: Session,
    key: str,
    year: int | None,
    quarter: int | None,
    month: int | None,
    date_from: date | None,
    date_to: date | None,
):
    try:
        return reports_service.build_report(
            session, key, year=year, quarter=quarter, month=month, date_from=date_from, date_to=date_to
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


@router.get("/{key}")
def report(
    key: str,
    year: int | None = Query(default=None, ge=2000, le=2100),
    quarter: int | None = Query(default=None, ge=1, le=4),
    month: int | None = Query(default=None, ge=1, le=12),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    _: CurrentUser = Depends(get_current_context),
    session: Session = Depends(db_session),
) -> dict:
    definition = _build(session, key, year, quarter, month, date_from, date_to)
    return {
        "key": definition.key,
        "title": definition.title,
        "columns": [{"key": col, "title": title, "type": kind} for col, title, kind in definition.columns],
        "rows": definition.rows,
        "summary": definition.summary,
    }


@router.get("/{key}/export")
def export_report(
    key: str,
    format: str = Query(default="csv", pattern="^(csv|xlsx|pdf)$"),
    year: int | None = Query(default=None, ge=2000, le=2100),
    quarter: int | None = Query(default=None, ge=1, le=4),
    month: int | None = Query(default=None, ge=1, le=12),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    _: CurrentUser = Depends(get_current_context),
    session: Session = Depends(db_session),
) -> Response:
    definition = _build(session, key, year, quarter, month, date_from, date_to)
    media_type, extension, _renderer = export_service.EXPORT_FORMATS[format]
    if format == "pdf":
        period = f"{date_from} - {date_to}" if date_from and date_to else str(year or "")
        content = export_service.report_to_pdf(definition, period_label=period)
    else:
        content = export_service.EXPORT_FORMATS[format][2](definition)
    filename = f"{definition.key}.{extension}"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
