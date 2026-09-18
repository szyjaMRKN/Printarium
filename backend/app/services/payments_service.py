"""Płatności do sprzedaży."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.dates import utcnow
from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.enums import AuditAction
from app.models.payment import Payment
from app.models.user import User
from app.repositories import sales_repo
from app.schemas.sale import PaymentCreate
from app.services import audit_service, sales_service


def add_payment(
    session: Session, sale_id: int, data: PaymentCreate, user: User | None, *, ip: str | None = None
) -> Payment:
    sale = sales_repo.get_sale(session, sale_id)
    if sale is None:
        raise NotFoundError("Nie znaleziono sprzedaży.")
    if sale.is_cancelled:
        raise ConflictError("Nie można dodać płatności do anulowanej sprzedaży.")

    if data.amount_gr < 0 and sale.paid_amount_gr + data.amount_gr < 0:
        raise ValidationError("Zwrot nie może przekroczyć sumy wpłat dla tej sprzedaży.")

    payment = Payment(
        sale_id=sale.id,
        payment_date=data.payment_date,
        amount_gr=data.amount_gr,
        method=data.method.value,
        description=data.description,
        created_by_id=user.id if user else None,
    )
    session.add(payment)
    sale.payments.append(payment)
    session.flush()
    sales_service.recalculate(session, sale)
    audit_service.record(
        session,
        AuditAction.PAYMENT_CREATE,
        user=user,
        entity_type="payment",
        entity_id=payment.id,
        ip_address=ip,
        description=f"Płatność {payment.amount_gr} gr do sprzedaży {sale.document_number}.",
        meta={"sale_id": sale.id, "amount_gr": payment.amount_gr},
    )
    return payment


def delete_payment(
    session: Session, payment_id: int, user: User | None, *, ip: str | None = None
) -> Payment:
    payment = session.get(Payment, payment_id)
    if payment is None or payment.deleted_at is not None:
        raise NotFoundError("Nie znaleziono płatności.")
    payment.deleted_at = utcnow()
    session.flush()
    sale = sales_repo.get_sale(session, payment.sale_id, include_deleted=True)
    if sale is not None:
        session.refresh(sale)
        sales_service.recalculate(session, sale)
    audit_service.record(
        session,
        AuditAction.PAYMENT_DELETE,
        user=user,
        entity_type="payment",
        entity_id=payment.id,
        ip_address=ip,
        description=f"Usunięto płatność {payment.amount_gr} gr (sprzedaż {payment.sale_id}).",
    )
    return payment
