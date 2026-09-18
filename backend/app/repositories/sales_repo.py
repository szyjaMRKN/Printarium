"""Zapytania o sprzedaż — filtry, sortowanie, paginacja."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.sale import Sale, SaleItem

SORTABLE = {
    "sale_date": Sale.sale_date,
    "document_number": Sale.document_number,
    "total_gr": Sale.total_gr,
    "accrued_revenue_gr": Sale.accrued_revenue_gr,
    "paid_amount_gr": Sale.paid_amount_gr,
    "payment_status": Sale.payment_status,
    "created_at": Sale.created_at,
}


@dataclass
class SaleFilters:
    date_from: date | None = None
    date_to: date | None = None
    year: int | None = None
    quarter: int | None = None
    month: int | None = None
    day: date | None = None
    product_id: int | None = None
    product_query: str | None = None
    sales_channel: str | None = None
    payment_method: str | None = None
    payment_status: str | None = None
    customer_type: str | None = None
    search: str | None = None
    include_deleted: bool = False
    include_cancelled: bool = True
    statuses: list[str] = field(default_factory=list)


def base_query(filters: SaleFilters) -> Select[tuple[Sale]]:
    from app.core.dates import month_range, quarter_range, year_range

    stmt = select(Sale)
    if not filters.include_deleted:
        stmt = stmt.where(Sale.deleted_at.is_(None))
    if not filters.include_cancelled:
        stmt = stmt.where(Sale.is_cancelled.is_(False))

    date_from, date_to = filters.date_from, filters.date_to
    if filters.day:
        date_from = date_to = filters.day
    elif filters.year and filters.quarter:
        date_from, date_to = quarter_range(filters.year, filters.quarter)
    elif filters.year and filters.month:
        date_from, date_to = month_range(filters.year, filters.month)
    elif filters.year:
        date_from, date_to = year_range(filters.year)

    if date_from:
        stmt = stmt.where(Sale.sale_date >= date_from)
    if date_to:
        stmt = stmt.where(Sale.sale_date <= date_to)
    if filters.sales_channel:
        stmt = stmt.where(Sale.sales_channel == filters.sales_channel)
    if filters.payment_method:
        stmt = stmt.where(Sale.payment_method == filters.payment_method)
    if filters.payment_status:
        stmt = stmt.where(Sale.payment_status == filters.payment_status)
    if filters.statuses:
        stmt = stmt.where(Sale.payment_status.in_(filters.statuses))
    if filters.customer_type:
        stmt = stmt.where(Sale.customer_type == filters.customer_type)
    if filters.product_id:
        stmt = stmt.where(Sale.id.in_(select(SaleItem.sale_id).where(SaleItem.product_id == filters.product_id)))
    if filters.product_query:
        pattern = f"%{filters.product_query.strip()}%"
        stmt = stmt.where(Sale.id.in_(select(SaleItem.sale_id).where(SaleItem.name.ilike(pattern))))
    if filters.search:
        pattern = f"%{filters.search.strip()}%"
        stmt = stmt.where(
            or_(
                Sale.document_number.ilike(pattern),
                Sale.description.ilike(pattern),
                Sale.customer_name.ilike(pattern),
                Sale.notes.ilike(pattern),
                Sale.id.in_(select(SaleItem.sale_id).where(SaleItem.name.ilike(pattern))),
            )
        )
    return stmt


def with_relations(stmt: Select[tuple[Sale]]) -> Select[tuple[Sale]]:
    return stmt.options(
        selectinload(Sale.items),
        selectinload(Sale.payments),
        selectinload(Sale.corrections),
    )


def apply_sort(stmt: Select[tuple[Sale]], sort_by: str, sort_dir: str) -> Select[tuple[Sale]]:
    column = SORTABLE.get(sort_by, Sale.sale_date)
    if sort_dir == "asc":
        return stmt.order_by(column.asc(), Sale.id.asc())
    return stmt.order_by(column.desc(), Sale.id.desc())


def get_sale(session: Session, sale_id: int, *, include_deleted: bool = False) -> Sale | None:
    stmt = with_relations(select(Sale).where(Sale.id == sale_id))
    if not include_deleted:
        stmt = stmt.where(Sale.deleted_at.is_(None))
    return session.execute(stmt).unique().scalar_one_or_none()
