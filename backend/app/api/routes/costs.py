"""Koszty, kategorie kosztów i załączniki."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, db_session, get_current_context, require_write
from app.repositories.base import paginate
from app.schemas.common import MessageResponse, PageMeta, PageResponse
from app.schemas.cost import (
    AttachmentOut,
    CostCategoryCreate,
    CostCategoryOut,
    CostCategoryUpdate,
    CostCreate,
    CostOut,
    CostUpdate,
)
from app.services import attachments_service, costs_service

router = APIRouter(tags=["koszty"])


def _to_out(cost) -> CostOut:
    data = CostOut.model_validate(cost)
    data.category_name = cost.category.name if cost.category else None
    data.attachment_name = cost.attachment.original_name if cost.attachment else None
    return data


@router.get("/costs", response_model=PageResponse[CostOut])
def list_costs(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    year: int | None = Query(default=None, ge=2000, le=2100),
    quarter: int | None = Query(default=None, ge=1, le=4),
    month: int | None = Query(default=None, ge=1, le=12),
    category_id: int | None = Query(default=None),
    payment_method: str | None = Query(default=None, max_length=32),
    search: str | None = Query(default=None, max_length=200),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=200),
    _: CurrentUser = Depends(get_current_context),
    session: Session = Depends(db_session),
) -> PageResponse[CostOut]:
    stmt = costs_service.query(
        date_from=date_from,
        date_to=date_to,
        year=year,
        quarter=quarter,
        month=month,
        category_id=category_id,
        payment_method=payment_method,
        search=search,
    )
    result = paginate(session, stmt, page, per_page)
    return PageResponse[CostOut](
        items=[_to_out(cost) for cost in result.items],
        meta=PageMeta(total=result.total, page=result.page, per_page=result.per_page, pages=result.pages),
    )


@router.post("/costs", response_model=CostOut, status_code=201)
def create_cost(
    payload: CostCreate,
    context: CurrentUser = Depends(require_write),
    session: Session = Depends(db_session),
) -> CostOut:
    cost = costs_service.create_cost(session, payload, context.user, ip=context.ip)
    session.commit()
    return _to_out(costs_service.get_cost(session, cost.id))


@router.get("/costs/{cost_id}", response_model=CostOut)
def get_cost(
    cost_id: int,
    _: CurrentUser = Depends(get_current_context),
    session: Session = Depends(db_session),
) -> CostOut:
    return _to_out(costs_service.get_cost(session, cost_id))


@router.put("/costs/{cost_id}", response_model=CostOut)
def update_cost(
    cost_id: int,
    payload: CostUpdate,
    context: CurrentUser = Depends(require_write),
    session: Session = Depends(db_session),
) -> CostOut:
    cost = costs_service.update_cost(session, cost_id, payload, context.user, ip=context.ip)
    session.commit()
    return _to_out(cost)


@router.delete("/costs/{cost_id}", response_model=MessageResponse)
def delete_cost(
    cost_id: int,
    context: CurrentUser = Depends(require_write),
    session: Session = Depends(db_session),
) -> MessageResponse:
    costs_service.soft_delete_cost(session, cost_id, context.user, ip=context.ip)
    session.commit()
    return MessageResponse(message="Koszt został oznaczony jako usunięty.")


# --- kategorie ---


@router.get("/cost-categories", response_model=list[CostCategoryOut])
def list_categories(
    _: CurrentUser = Depends(get_current_context), session: Session = Depends(db_session)
) -> list[CostCategoryOut]:
    return [CostCategoryOut.model_validate(item) for item in costs_service.list_categories(session)]


@router.post("/cost-categories", response_model=CostCategoryOut, status_code=201)
def create_category(
    payload: CostCategoryCreate,
    context: CurrentUser = Depends(require_write),
    session: Session = Depends(db_session),
) -> CostCategoryOut:
    category = costs_service.create_category(session, payload, context.user)
    session.commit()
    return CostCategoryOut.model_validate(category)


@router.put("/cost-categories/{category_id}", response_model=CostCategoryOut)
def update_category(
    category_id: int,
    payload: CostCategoryUpdate,
    context: CurrentUser = Depends(require_write),
    session: Session = Depends(db_session),
) -> CostCategoryOut:
    category = costs_service.update_category(session, category_id, payload, context.user)
    session.commit()
    return CostCategoryOut.model_validate(category)


@router.delete("/cost-categories/{category_id}", response_model=MessageResponse)
def delete_category(
    category_id: int,
    context: CurrentUser = Depends(require_write),
    session: Session = Depends(db_session),
) -> MessageResponse:
    costs_service.delete_category(session, category_id, context.user)
    session.commit()
    return MessageResponse(message="Kategoria została usunięta.")


# --- załączniki ---


@router.post("/attachments", response_model=AttachmentOut, status_code=201)
async def upload_attachment(
    file: UploadFile = File(...),
    context: CurrentUser = Depends(require_write),
    session: Session = Depends(db_session),
) -> AttachmentOut:
    content = await file.read()
    attachment = attachments_service.store_upload(
        session,
        filename=file.filename or "plik",
        content_type=file.content_type or "",
        content=content,
        user=context.user,
        ip=context.ip,
    )
    session.commit()
    return AttachmentOut.model_validate(attachment)


@router.get("/attachments/{attachment_id}")
def download_attachment(
    attachment_id: int,
    _: CurrentUser = Depends(get_current_context),
    session: Session = Depends(db_session),
) -> FileResponse:
    attachment = attachments_service.get_attachment(session, attachment_id)
    path = attachments_service.attachment_path(attachment)
    return FileResponse(
        path,
        media_type=attachment.content_type,
        filename=attachment.original_name,
        headers={"Content-Disposition": f'attachment; filename="{attachment.stored_name}"'},
    )
