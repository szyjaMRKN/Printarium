"""Sprzedaż, płatności, korekty i ewidencja."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, db_session, get_current_context, require_write
from app.core.errors import NotFoundError
from app.repositories import sales_repo
from app.repositories.base import paginate
from app.repositories.sales_repo import SaleFilters
from app.schemas.common import MessageResponse, PageMeta, PageResponse
from app.schemas.sale import (
    CorrectionCreate,
    CorrectionOut,
    DailyRegistryRow,
    PaymentCreate,
    PaymentOut,
    RegistryRow,
    SaleCreate,
    SaleListItem,
    SaleOut,
    SaleUpdate,
)
from app.services import corrections_service, payments_service, reports_service, sales_service

router = APIRouter(tags=["sprzedaz"])


def _filters(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    day: date | None = Query(default=None),
    year: int | None = Query(default=None, ge=2000, le=2100),
    quarter: int | None = Query(default=None, ge=1, le=4),
    month: int | None = Query(default=None, ge=1, le=12),
    product_id: int | None = Query(default=None),
    product: str | None = Query(default=None, max_length=200),
    sales_channel: str | None = Query(default=None, max_length=32),
    payment_method: str | None = Query(default=None, max_length=32),
    payment_status: str | None = Query(default=None, max_length=32),
    customer_type: str | None = Query(default=None, max_length=8),
    search: str | None = Query(default=None, max_length=200),
) -> SaleFilters:
    return SaleFilters(
        date_from=date_from,
        date_to=date_to,
        day=day,
        year=year,
        quarter=quarter,
        month=month,
        product_id=product_id,
        product_query=product,
        sales_channel=sales_channel,
        payment_method=payment_method,
        payment_status=payment_status,
        customer_type=customer_type,
        search=search,
    )


@router.get("/sales", response_model=PageResponse[SaleListItem])
def list_sales(
    filters: SaleFilters = Depends(_filters),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=200),
    sort_by: str = Query(default="sale_date"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    _: CurrentUser = Depends(get_current_context),
    session: Session = Depends(db_session),
) -> PageResponse[SaleListItem]:
    stmt = sales_repo.apply_sort(sales_repo.base_query(filters), sort_by, sort_dir)
    result = paginate(session, stmt, page, per_page)
    return PageResponse[SaleListItem](
        items=[SaleListItem.model_validate(sale) for sale in result.items],
        meta=PageMeta(total=result.total, page=result.page, per_page=result.per_page, pages=result.pages),
    )


@router.post("/sales", response_model=SaleOut, status_code=201)
def create_sale(
    payload: SaleCreate,
    context: CurrentUser = Depends(require_write),
    session: Session = Depends(db_session),
) -> SaleOut:
    sale = sales_service.create_sale(session, payload, context.user, ip=context.ip)
    session.commit()
    sale = sales_repo.get_sale(session, sale.id)
    return SaleOut.model_validate(sale)


@router.get("/sales/{sale_id}", response_model=SaleOut)
def get_sale(
    sale_id: int,
    _: CurrentUser = Depends(get_current_context),
    session: Session = Depends(db_session),
) -> SaleOut:
    sale = sales_repo.get_sale(session, sale_id)
    if sale is None:
        raise NotFoundError("Nie znaleziono sprzedaży.")
    return SaleOut.model_validate(sale)


@router.put("/sales/{sale_id}", response_model=SaleOut)
def update_sale(
    sale_id: int,
    payload: SaleUpdate,
    context: CurrentUser = Depends(require_write),
    session: Session = Depends(db_session),
) -> SaleOut:
    sale = sales_service.update_sale(session, sale_id, payload, context.user, ip=context.ip)
    session.commit()
    sale = sales_repo.get_sale(session, sale.id)
    return SaleOut.model_validate(sale)


@router.delete("/sales/{sale_id}", response_model=MessageResponse)
def delete_sale(
    sale_id: int,
    reason: str | None = Query(default=None, max_length=200),
    context: CurrentUser = Depends(require_write),
    session: Session = Depends(db_session),
) -> MessageResponse:
    sales_service.soft_delete_sale(session, sale_id, context.user, reason=reason, ip=context.ip)
    session.commit()
    return MessageResponse(message="Sprzedaż została oznaczona jako usunięta (dane pozostają w historii).")


@router.post("/sales/{sale_id}/restore", response_model=SaleOut)
def restore_sale(
    sale_id: int,
    context: CurrentUser = Depends(require_write),
    session: Session = Depends(db_session),
) -> SaleOut:
    sale = sales_service.restore_sale(session, sale_id, context.user, ip=context.ip)
    session.commit()
    return SaleOut.model_validate(sale)


# --- płatności ---


@router.post("/sales/{sale_id}/payments", response_model=SaleOut, status_code=201)
def add_payment(
    sale_id: int,
    payload: PaymentCreate,
    context: CurrentUser = Depends(require_write),
    session: Session = Depends(db_session),
) -> SaleOut:
    payments_service.add_payment(session, sale_id, payload, context.user, ip=context.ip)
    session.commit()
    return SaleOut.model_validate(sales_repo.get_sale(session, sale_id))


@router.get("/sales/{sale_id}/payments", response_model=list[PaymentOut])
def list_payments(
    sale_id: int,
    _: CurrentUser = Depends(get_current_context),
    session: Session = Depends(db_session),
) -> list[PaymentOut]:
    sale = sales_repo.get_sale(session, sale_id)
    if sale is None:
        raise NotFoundError("Nie znaleziono sprzedaży.")
    return [PaymentOut.model_validate(p) for p in sale.payments if p.deleted_at is None]


@router.delete("/payments/{payment_id}", response_model=MessageResponse)
def delete_payment(
    payment_id: int,
    context: CurrentUser = Depends(require_write),
    session: Session = Depends(db_session),
) -> MessageResponse:
    payments_service.delete_payment(session, payment_id, context.user, ip=context.ip)
    session.commit()
    return MessageResponse(message="Płatność została usunięta, a status sprzedaży przeliczony.")


# --- korekty ---


@router.post("/sales/{sale_id}/corrections", response_model=SaleOut, status_code=201)
def add_correction(
    sale_id: int,
    payload: CorrectionCreate,
    context: CurrentUser = Depends(require_write),
    session: Session = Depends(db_session),
) -> SaleOut:
    corrections_service.add_correction(session, sale_id, payload, context.user, ip=context.ip)
    session.commit()
    return SaleOut.model_validate(sales_repo.get_sale(session, sale_id))


@router.get("/sales/{sale_id}/corrections", response_model=list[CorrectionOut])
def list_corrections(
    sale_id: int,
    _: CurrentUser = Depends(get_current_context),
    session: Session = Depends(db_session),
) -> list[CorrectionOut]:
    return [
        CorrectionOut.model_validate(item)
        for item in corrections_service.list_corrections(session, sale_id)
    ]


# --- ewidencja ---


@router.get("/registry")
def registry(
    filters: SaleFilters = Depends(_filters),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=500),
    _: CurrentUser = Depends(get_current_context),
    session: Session = Depends(db_session),
) -> dict:
    result = reports_service.sales_registry(session, filters, page=page, per_page=per_page)
    return {
        "items": [RegistryRow(**row).model_dump() for row in result.rows],
        "meta": {
            "total": result.total_count,
            "page": result.page,
            "per_page": result.per_page,
            "pages": (result.total_count + result.per_page - 1) // result.per_page,
        },
        "summary": {"accrued_revenue_gr": result.total_accrued_gr},
    }


@router.get("/registry/daily", response_model=list[DailyRegistryRow])
def registry_daily(
    filters: SaleFilters = Depends(_filters),
    _: CurrentUser = Depends(get_current_context),
    session: Session = Depends(db_session),
) -> list[DailyRegistryRow]:
    return [DailyRegistryRow(**row) for row in reports_service.daily_registry(session, filters)]
