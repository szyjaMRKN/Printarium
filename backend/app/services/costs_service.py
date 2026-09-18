"""Koszty i kategorie kosztów."""

from __future__ import annotations

import re
import unicodedata
from datetime import date

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.dates import month_range, quarter_range, utcnow, year_range
from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.cost import Cost, CostCategory
from app.models.enums import AuditAction
from app.models.user import User
from app.schemas.cost import CostCategoryCreate, CostCategoryUpdate, CostCreate, CostUpdate
from app.services import audit_service

DEFAULT_CATEGORIES = [
    "Materiały",
    "Opakowania",
    "Elektronika",
    "Narzędzia",
    "Wysyłka",
    "Reklama",
    "Prowizje",
    "Oprogramowanie",
    "Inne",
]


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.replace("ł", "l").replace("Ł", "L"))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
    return slug or "kategoria"


def ensure_default_categories(session: Session) -> None:
    existing = session.execute(select(CostCategory.slug)).scalars().all()
    if existing:
        return
    for index, name in enumerate(DEFAULT_CATEGORIES, start=1):
        session.add(CostCategory(name=name, slug=slugify(name), sort_order=index * 10))
    session.flush()


def list_categories(session: Session, include_inactive: bool = True) -> list[CostCategory]:
    stmt = select(CostCategory).where(CostCategory.deleted_at.is_(None))
    if not include_inactive:
        stmt = stmt.where(CostCategory.is_active.is_(True))
    return list(session.execute(stmt.order_by(CostCategory.sort_order, CostCategory.name)).scalars())


def create_category(session: Session, data: CostCategoryCreate, user: User | None) -> CostCategory:
    slug = slugify(data.name)
    exists = session.execute(
        select(CostCategory.id).where(CostCategory.slug == slug, CostCategory.deleted_at.is_(None))
    ).scalar_one_or_none()
    if exists:
        raise ConflictError("Kategoria o takiej nazwie już istnieje.")
    category = CostCategory(name=data.name.strip(), slug=slug, is_active=data.is_active, sort_order=data.sort_order)
    session.add(category)
    session.flush()
    audit_service.record(
        session,
        AuditAction.SETTINGS_UPDATE,
        user=user,
        entity_type="cost_category",
        entity_id=category.id,
        description=f"Dodano kategorię kosztów {category.name}.",
    )
    return category


def update_category(
    session: Session, category_id: int, data: CostCategoryUpdate, user: User | None
) -> CostCategory:
    category = session.get(CostCategory, category_id)
    if category is None or category.deleted_at is not None:
        raise NotFoundError("Nie znaleziono kategorii.")
    if data.name:
        category.name = data.name.strip()
        category.slug = slugify(category.name)
    if data.is_active is not None:
        category.is_active = data.is_active
    if data.sort_order is not None:
        category.sort_order = data.sort_order
    session.flush()
    audit_service.record(
        session,
        AuditAction.SETTINGS_UPDATE,
        user=user,
        entity_type="cost_category",
        entity_id=category.id,
        description=f"Zmieniono kategorię kosztów {category.name}.",
    )
    return category


def delete_category(session: Session, category_id: int, user: User | None) -> None:
    category = session.get(CostCategory, category_id)
    if category is None or category.deleted_at is not None:
        raise NotFoundError("Nie znaleziono kategorii.")
    in_use = session.execute(
        select(Cost.id).where(Cost.category_id == category_id, Cost.deleted_at.is_(None)).limit(1)
    ).scalar_one_or_none()
    if in_use:
        raise ConflictError("Kategoria jest używana w kosztach — możesz ją tylko dezaktywować.")
    category.deleted_at = utcnow()
    session.flush()
    audit_service.record(
        session,
        AuditAction.SETTINGS_UPDATE,
        user=user,
        entity_type="cost_category",
        entity_id=category_id,
        description=f"Usunięto kategorię kosztów {category.name}.",
    )


def query(
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    year: int | None = None,
    quarter: int | None = None,
    month: int | None = None,
    category_id: int | None = None,
    payment_method: str | None = None,
    search: str | None = None,
) -> Select:
    stmt = (
        select(Cost)
        .options(selectinload(Cost.category), selectinload(Cost.attachment))
        .where(Cost.deleted_at.is_(None))
        .order_by(Cost.cost_date.desc(), Cost.id.desc())
    )
    if year and quarter:
        date_from, date_to = quarter_range(year, quarter)
    elif year and month:
        date_from, date_to = month_range(year, month)
    elif year:
        date_from, date_to = year_range(year)
    if date_from:
        stmt = stmt.where(Cost.cost_date >= date_from)
    if date_to:
        stmt = stmt.where(Cost.cost_date <= date_to)
    if category_id:
        stmt = stmt.where(Cost.category_id == category_id)
    if payment_method:
        stmt = stmt.where(Cost.payment_method == payment_method)
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(Cost.name.ilike(pattern), Cost.vendor.ilike(pattern), Cost.invoice_number.ilike(pattern))
        )
    return stmt


def get_cost(session: Session, cost_id: int) -> Cost:
    cost = session.get(Cost, cost_id)
    if cost is None or cost.deleted_at is not None:
        raise NotFoundError("Nie znaleziono kosztu.")
    return cost


def _validate_category(session: Session, category_id: int | None) -> None:
    if category_id is None:
        return
    category = session.get(CostCategory, category_id)
    if category is None or category.deleted_at is not None:
        raise ValidationError("Wybrana kategoria kosztów nie istnieje.")


def create_cost(session: Session, data: CostCreate, user: User | None, *, ip: str | None = None) -> Cost:
    _validate_category(session, data.category_id)
    payload = data.model_dump()
    payload["payment_method"] = data.payment_method.value if data.payment_method else None
    cost = Cost(**payload, created_by_id=user.id if user else None)
    session.add(cost)
    session.flush()
    audit_service.record(
        session,
        AuditAction.COST_CREATE,
        user=user,
        entity_type="cost",
        entity_id=cost.id,
        ip_address=ip,
        description=f"Dodano koszt {cost.name} na kwotę {cost.amount_gr} gr.",
    )
    return cost


def update_cost(
    session: Session, cost_id: int, data: CostUpdate, user: User | None, *, ip: str | None = None
) -> Cost:
    cost = get_cost(session, cost_id)
    _validate_category(session, data.category_id)
    previous_amount = cost.amount_gr
    payload = data.model_dump()
    payload["payment_method"] = data.payment_method.value if data.payment_method else None
    for key, value in payload.items():
        setattr(cost, key, value)
    session.flush()
    audit_service.record(
        session,
        AuditAction.COST_UPDATE,
        user=user,
        entity_type="cost",
        entity_id=cost.id,
        ip_address=ip,
        description=f"Zmieniono koszt {cost.name}: {previous_amount} gr -> {cost.amount_gr} gr.",
    )
    return cost


def soft_delete_cost(session: Session, cost_id: int, user: User | None, *, ip: str | None = None) -> Cost:
    cost = get_cost(session, cost_id)
    cost.deleted_at = utcnow()
    session.flush()
    audit_service.record(
        session,
        AuditAction.COST_DELETE,
        user=user,
        entity_type="cost",
        entity_id=cost.id,
        ip_address=ip,
        description=f"Usunięto (miękko) koszt {cost.name}.",
    )
    return cost
