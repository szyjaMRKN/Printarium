"""Baza produktów."""

from __future__ import annotations

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.core.dates import utcnow
from app.core.errors import ConflictError, NotFoundError
from app.models.enums import AuditAction
from app.models.product import Product
from app.models.sale import SaleItem
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate
from app.services import audit_service


def query(search: str | None = None, only_active: bool = False, include_deleted: bool = False) -> Select:
    stmt = select(Product).order_by(Product.name.asc())
    if not include_deleted:
        stmt = stmt.where(Product.deleted_at.is_(None))
    if only_active:
        stmt = stmt.where(Product.is_active.is_(True))
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(Product.name.ilike(pattern), Product.sku.ilike(pattern), Product.model.ilike(pattern))
        )
    return stmt


def get_product(session: Session, product_id: int) -> Product:
    product = session.get(Product, product_id)
    if product is None or product.deleted_at is not None:
        raise NotFoundError("Nie znaleziono produktu.")
    return product


def _check_sku(session: Session, sku: str | None, product_id: int | None = None) -> None:
    if not sku:
        return
    stmt = select(Product.id).where(Product.sku == sku, Product.deleted_at.is_(None))
    if product_id:
        stmt = stmt.where(Product.id != product_id)
    if session.execute(stmt.limit(1)).scalar_one_or_none() is not None:
        raise ConflictError(f"Produkt o SKU {sku} już istnieje.")


def create_product(session: Session, data: ProductCreate, user: User | None, *, ip: str | None = None) -> Product:
    _check_sku(session, data.sku)
    product = Product(**data.model_dump())
    session.add(product)
    session.flush()
    audit_service.record(
        session,
        AuditAction.PRODUCT_CREATE,
        user=user,
        entity_type="product",
        entity_id=product.id,
        ip_address=ip,
        description=f"Dodano produkt {product.name}.",
    )
    return product


def update_product(
    session: Session, product_id: int, data: ProductUpdate, user: User | None, *, ip: str | None = None
) -> Product:
    product = get_product(session, product_id)
    _check_sku(session, data.sku, product_id)
    for key, value in data.model_dump().items():
        setattr(product, key, value)
    session.flush()
    audit_service.record(
        session,
        AuditAction.PRODUCT_UPDATE,
        user=user,
        entity_type="product",
        entity_id=product.id,
        ip_address=ip,
        description=f"Zmieniono produkt {product.name}.",
    )
    return product


def soft_delete_product(session: Session, product_id: int, user: User | None, *, ip: str | None = None) -> Product:
    product = get_product(session, product_id)
    product.deleted_at = utcnow()
    product.is_active = False
    session.flush()
    audit_service.record(
        session,
        AuditAction.PRODUCT_DELETE,
        user=user,
        entity_type="product",
        entity_id=product.id,
        ip_address=ip,
        description=f"Usunięto (miękko) produkt {product.name}.",
    )
    return product


def usage_count(session: Session, product_id: int) -> int:
    return int(
        session.execute(
            select(func.count(SaleItem.id)).where(SaleItem.product_id == product_id)
        ).scalar_one()
    )
