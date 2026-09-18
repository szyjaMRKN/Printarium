"""Produkty."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, db_session, get_current_context, require_write
from app.repositories.base import paginate
from app.schemas.common import MessageResponse, PageMeta, PageResponse
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate
from app.services import products_service

router = APIRouter(prefix="/products", tags=["produkty"])


@router.get("", response_model=PageResponse[ProductOut])
def list_products(
    search: str | None = Query(default=None, max_length=200),
    only_active: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    _: CurrentUser = Depends(get_current_context),
    session: Session = Depends(db_session),
) -> PageResponse[ProductOut]:
    stmt = products_service.query(search=search, only_active=only_active)
    result = paginate(session, stmt, page, per_page)
    return PageResponse[ProductOut](
        items=[ProductOut.model_validate(item) for item in result.items],
        meta=PageMeta(total=result.total, page=result.page, per_page=result.per_page, pages=result.pages),
    )


@router.post("", response_model=ProductOut, status_code=201)
def create_product(
    payload: ProductCreate,
    context: CurrentUser = Depends(require_write),
    session: Session = Depends(db_session),
) -> ProductOut:
    product = products_service.create_product(session, payload, context.user, ip=context.ip)
    session.commit()
    return ProductOut.model_validate(product)


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: int,
    _: CurrentUser = Depends(get_current_context),
    session: Session = Depends(db_session),
) -> ProductOut:
    return ProductOut.model_validate(products_service.get_product(session, product_id))


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    context: CurrentUser = Depends(require_write),
    session: Session = Depends(db_session),
) -> ProductOut:
    product = products_service.update_product(session, product_id, payload, context.user, ip=context.ip)
    session.commit()
    return ProductOut.model_validate(product)


@router.delete("/{product_id}", response_model=MessageResponse)
def delete_product(
    product_id: int,
    context: CurrentUser = Depends(require_write),
    session: Session = Depends(db_session),
) -> MessageResponse:
    products_service.soft_delete_product(session, product_id, context.user, ip=context.ip)
    session.commit()
    return MessageResponse(message="Produkt został oznaczony jako usunięty.")
