"""Logika sprzedaży: sumy, przychód należny, statusy płatności.

To jest jedyne miejsce, w którym zmieniają się kwoty denormalizowane na
sprzedaży (accrued_revenue_gr, paid_amount_gr, payment_status).
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.dates import utcnow
from app.models.enums import AuditAction, CorrectionType, PaymentStatus
from app.models.payment import Payment
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.models.user import User
from app.repositories import sales_repo
from app.schemas.sale import InitialPaymentIn, SaleCreate, SaleItemIn, SaleUpdate
from app.services import audit_service
from app.services.settings_service import SettingsService

REFUND_TYPES = {CorrectionType.FULL_RETURN.value, CorrectionType.PARTIAL_RETURN.value}


def compute_items_total(items: list[SaleItemIn]) -> int:
    return sum(item.quantity * item.unit_price_gr for item in items)


def compute_total(items_total_gr: int, discount_gr: int, shipping_gr: int) -> int:
    """Wartość całkowita = produkty - rabat + wysyłka."""
    return items_total_gr - discount_gr + shipping_gr


def build_description(items: list[SaleItemIn]) -> str:
    parts = [f"{item.name} x{item.quantity}" for item in items[:4]]
    if len(items) > 4:
        parts.append(f"i {len(items) - 4} poz. więcej")
    return ", ".join(parts)[:300]


def next_document_number(session: Session, sale_date: date) -> str:
    year = sale_date.year
    pattern = f"SPR/{year}/%"
    count = int(
        session.execute(
            select(func.count(Sale.id)).where(Sale.document_number.like(pattern))
        ).scalar_one()
    )
    seq = count + 1
    while True:
        candidate = f"SPR/{year}/{seq:04d}"
        exists = session.execute(
            select(Sale.id).where(Sale.document_number == candidate).limit(1)
        ).scalar_one_or_none()
        if exists is None:
            return candidate
        seq += 1


def _ensure_unique_number(session: Session, number: str | None, *, sale_id: int | None = None) -> None:
    if not number:
        return
    stmt = select(Sale.id).where(Sale.document_number == number, Sale.deleted_at.is_(None))
    if sale_id is not None:
        stmt = stmt.where(Sale.id != sale_id)
    if session.execute(stmt.limit(1)).scalar_one_or_none() is not None:
        raise ConflictError(f"Sprzedaż o numerze {number} już istnieje.")


def _validate_amounts(items_total_gr: int, discount_gr: int) -> None:
    if discount_gr > items_total_gr:
        raise ValidationError("Rabat nie może być większy niż wartość produktów.")


def _apply_items(session: Session, sale: Sale, items: list[SaleItemIn]) -> None:
    sale.items.clear()
    session.flush()
    for position, item in enumerate(items, start=1):
        product_id = item.product_id
        if product_id is not None:
            product = session.get(Product, product_id)
            if product is None or product.deleted_at is not None:
                raise ValidationError(f"Produkt o identyfikatorze {product_id} nie istnieje.")
        sale.items.append(
            SaleItem(
                product_id=product_id,
                position=position,
                name=item.name,
                variant=item.variant,
                quantity=item.quantity,
                unit_price_gr=item.unit_price_gr,
                line_total_gr=item.quantity * item.unit_price_gr,
            )
        )
    session.flush()


def revenue_base_gr(sale: Sale, *, shipping_counts: bool) -> int:
    """Podstawa przychodu należnego przed korektami."""
    if shipping_counts:
        return sale.total_gr
    return sale.total_gr - sale.shipping_gr


def recalculate(session: Session, sale: Sale) -> Sale:
    """Przelicza korekty, płatności i status sprzedaży."""
    settings_service = SettingsService(session)
    shipping_counts = settings_service.get_bool("fiscal.shipping_counts_as_revenue")

    active_corrections = [c for c in sale.corrections if c.deleted_at is None]
    corrections_total = sum(c.amount_gr for c in active_corrections)
    sale.corrections_total_gr = corrections_total

    base = revenue_base_gr(sale, shipping_counts=shipping_counts)
    accrued = base + corrections_total
    if sale.is_cancelled:
        accrued = 0
    sale.accrued_revenue_gr = max(accrued, 0)

    active_payments = [p for p in sale.payments if p.deleted_at is None]
    sale.paid_amount_gr = sum(p.amount_gr for p in active_payments)
    inflows = sorted((p.payment_date for p in active_payments if p.amount_gr > 0))
    sale.first_payment_date = inflows[0] if inflows else None
    sale.last_payment_date = inflows[-1] if inflows else None

    has_refund_correction = any(c.correction_type in REFUND_TYPES for c in active_corrections)

    if sale.is_cancelled:
        sale.payment_status = PaymentStatus.CANCELLED.value
    elif sale.accrued_revenue_gr <= 0 and has_refund_correction:
        sale.payment_status = PaymentStatus.REFUNDED.value
    elif sale.paid_amount_gr >= sale.accrued_revenue_gr:
        sale.payment_status = PaymentStatus.PAID.value
    elif sale.paid_amount_gr > 0:
        sale.payment_status = PaymentStatus.PARTIAL.value
    else:
        sale.payment_status = PaymentStatus.UNPAID.value

    session.flush()
    return sale


def create_sale(session: Session, data: SaleCreate, user: User | None, *, ip: str | None = None) -> Sale:
    items_total = compute_items_total(data.items)
    _validate_amounts(items_total, data.discount_gr)
    number = data.document_number or next_document_number(session, data.sale_date)
    _ensure_unique_number(session, number)

    sale = Sale(
        document_number=number,
        sale_date=data.sale_date,
        description=data.description or build_description(data.items),
        items_total_gr=items_total,
        discount_gr=data.discount_gr,
        shipping_gr=data.shipping_gr,
        total_gr=compute_total(items_total, data.discount_gr, data.shipping_gr),
        payment_method=data.payment_method.value if data.payment_method else None,
        sales_channel=data.sales_channel.value if data.sales_channel else None,
        customer_type=data.customer_type.value,
        customer_name=data.customer_name,
        customer_nip=data.customer_nip,
        customer_email=data.customer_email,
        customer_phone=data.customer_phone,
        customer_address=data.customer_address,
        notes=data.notes,
        created_by_id=user.id if user else None,
    )
    session.add(sale)
    session.flush()
    _apply_items(session, sale, data.items)

    if data.initial_payment is not None:
        _add_initial_payment(session, sale, data.initial_payment, user)

    recalculate(session, sale)
    audit_service.record(
        session,
        AuditAction.SALE_CREATE,
        user=user,
        entity_type="sale",
        entity_id=sale.id,
        ip_address=ip,
        description=f"Dodano sprzedaż {sale.document_number} na kwotę {sale.total_gr} gr.",
        meta={"total_gr": sale.total_gr, "sale_date": sale.sale_date.isoformat()},
    )
    return sale


def _add_initial_payment(session: Session, sale: Sale, data: InitialPaymentIn, user: User | None) -> None:
    if data.amount_gr > sale.total_gr:
        raise ValidationError("Kwota płatności nie może przekraczać wartości sprzedaży.")
    sale.payments.append(
        Payment(
            payment_date=data.payment_date,
            amount_gr=data.amount_gr,
            method=data.method.value,
            description=data.description,
            created_by_id=user.id if user else None,
        )
    )
    session.flush()


def update_sale(
    session: Session, sale_id: int, data: SaleUpdate, user: User | None, *, ip: str | None = None
) -> Sale:
    sale = sales_repo.get_sale(session, sale_id)
    if sale is None:
        raise NotFoundError("Nie znaleziono sprzedaży.")
    if sale.is_cancelled:
        raise ConflictError("Sprzedaż jest anulowana — użyj korekty zamiast edycji.")

    items_total = compute_items_total(data.items)
    _validate_amounts(items_total, data.discount_gr)
    number = data.document_number or sale.document_number
    _ensure_unique_number(session, number, sale_id=sale.id)

    previous_total = sale.total_gr
    sale.document_number = number
    sale.sale_date = data.sale_date
    sale.description = data.description or build_description(data.items)
    sale.items_total_gr = items_total
    sale.discount_gr = data.discount_gr
    sale.shipping_gr = data.shipping_gr
    sale.total_gr = compute_total(items_total, data.discount_gr, data.shipping_gr)
    sale.payment_method = data.payment_method.value if data.payment_method else None
    sale.sales_channel = data.sales_channel.value if data.sales_channel else None
    sale.customer_type = data.customer_type.value
    sale.customer_name = data.customer_name
    sale.customer_nip = data.customer_nip
    sale.customer_email = data.customer_email
    sale.customer_phone = data.customer_phone
    sale.customer_address = data.customer_address
    sale.notes = data.notes
    _apply_items(session, sale, data.items)
    recalculate(session, sale)

    audit_service.record(
        session,
        AuditAction.SALE_UPDATE,
        user=user,
        entity_type="sale",
        entity_id=sale.id,
        ip_address=ip,
        description=f"Zmieniono sprzedaż {sale.document_number}: {previous_total} gr -> {sale.total_gr} gr.",
        meta={"previous_total_gr": previous_total, "total_gr": sale.total_gr},
    )
    return sale


def soft_delete_sale(
    session: Session, sale_id: int, user: User | None, *, reason: str | None = None, ip: str | None = None
) -> Sale:
    """Usunięcie miękkie — rekord zostaje w bazie i w historii."""
    sale = sales_repo.get_sale(session, sale_id)
    if sale is None:
        raise NotFoundError("Nie znaleziono sprzedaży.")
    sale.deleted_at = utcnow()
    if reason:
        sale.notes = f"{sale.notes}\n[usunięcie] {reason}" if sale.notes else f"[usunięcie] {reason}"
    session.flush()
    audit_service.record(
        session,
        AuditAction.SALE_DELETE,
        user=user,
        entity_type="sale",
        entity_id=sale.id,
        ip_address=ip,
        description=f"Usunięto (miękko) sprzedaż {sale.document_number}. Powód: {reason or 'nie podano'}.",
    )
    return sale


def restore_sale(session: Session, sale_id: int, user: User | None, *, ip: str | None = None) -> Sale:
    sale = sales_repo.get_sale(session, sale_id, include_deleted=True)
    if sale is None:
        raise NotFoundError("Nie znaleziono sprzedaży.")
    sale.deleted_at = None
    recalculate(session, sale)
    audit_service.record(
        session,
        AuditAction.SALE_UPDATE,
        user=user,
        entity_type="sale",
        entity_id=sale.id,
        ip_address=ip,
        description=f"Przywrócono sprzedaż {sale.document_number}.",
    )
    return sale
