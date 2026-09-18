"""Korekty sprzedaży: zwroty, rabaty po sprzedaży, anulowania, korekty wartości.

Nic nie jest kasowane — każda zmiana wartości zostawia ślad w tabeli korekt
razem z wartością poprzednią, nową i powodem.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.correction import Correction
from app.models.enums import AuditAction, CorrectionType, PaymentMethod
from app.models.payment import Payment
from app.models.user import User
from app.repositories import sales_repo
from app.schemas.sale import CorrectionCreate
from app.services import audit_service, sales_service


def _resolve_amounts(sale, data: CorrectionCreate) -> tuple[int, int, int]:
    """Zwraca (previous_value_gr, new_value_gr, amount_gr)."""
    previous = sale.accrued_revenue_gr
    kind = data.correction_type

    if kind in (CorrectionType.FULL_RETURN, CorrectionType.CANCELLATION):
        return previous, 0, -previous

    if kind in (CorrectionType.PARTIAL_RETURN, CorrectionType.POST_SALE_DISCOUNT):
        if not data.amount_gr:
            raise ValidationError("Podaj kwotę korekty.")
        if data.amount_gr > previous:
            raise ValidationError("Kwota korekty nie może przekraczać aktualnego przychodu należnego.")
        return previous, previous - data.amount_gr, -data.amount_gr

    if kind is CorrectionType.VALUE_CORRECTION:
        if data.new_value_gr is None:
            raise ValidationError("Podaj nową wartość sprzedaży.")
        return previous, data.new_value_gr, data.new_value_gr - previous

    if kind is CorrectionType.MONEY_REFUND:
        if data.refund_amount_gr <= 0:
            raise ValidationError("Podaj kwotę zwracaną klientowi.")
        return previous, previous, 0

    raise ValidationError("Nieobsługiwany rodzaj korekty.")


def add_correction(
    session: Session, sale_id: int, data: CorrectionCreate, user: User | None, *, ip: str | None = None
) -> Correction:
    sale = sales_repo.get_sale(session, sale_id)
    if sale is None:
        raise NotFoundError("Nie znaleziono sprzedaży.")
    if sale.is_cancelled:
        raise ConflictError("Sprzedaż jest już anulowana.")

    previous, new_value, amount = _resolve_amounts(sale, data)

    if data.refund_amount_gr:
        available = sale.paid_amount_gr
        if data.refund_amount_gr > available:
            raise ValidationError("Zwrot pieniędzy nie może przekroczyć sumy otrzymanych wpłat.")

    correction = Correction(
        sale_id=sale.id,
        correction_date=data.correction_date,
        correction_type=data.correction_type.value,
        previous_value_gr=previous,
        new_value_gr=max(new_value, 0),
        amount_gr=amount,
        refund_amount_gr=data.refund_amount_gr,
        reason=data.reason,
        description=data.description,
        created_by_id=user.id if user else None,
    )
    session.add(correction)
    sale.corrections.append(correction)
    session.flush()

    if data.correction_type is CorrectionType.CANCELLATION:
        sale.is_cancelled = True

    if data.refund_amount_gr:
        method = (data.refund_method or PaymentMethod(sale.payment_method or PaymentMethod.TRANSFER.value)).value
        refund = Payment(
            sale_id=sale.id,
            payment_date=data.correction_date,
            amount_gr=-data.refund_amount_gr,
            method=method,
            description=f"Zwrot pieniędzy klientowi (korekta #{correction.id}).",
            correction_id=correction.id,
            created_by_id=user.id if user else None,
        )
        session.add(refund)
        sale.payments.append(refund)
        session.flush()

    sales_service.recalculate(session, sale)
    audit_service.record(
        session,
        AuditAction.CORRECTION_CREATE,
        user=user,
        entity_type="correction",
        entity_id=correction.id,
        ip_address=ip,
        description=(
            f"Korekta '{correction.correction_type}' do sprzedaży {sale.document_number}: "
            f"{previous} gr -> {sale.accrued_revenue_gr} gr."
        ),
        meta={
            "sale_id": sale.id,
            "previous_value_gr": previous,
            "new_value_gr": sale.accrued_revenue_gr,
            "amount_gr": amount,
            "refund_amount_gr": data.refund_amount_gr,
        },
    )
    return correction


def list_corrections(session: Session, sale_id: int) -> list[Correction]:
    sale = sales_repo.get_sale(session, sale_id)
    if sale is None:
        raise NotFoundError("Nie znaleziono sprzedaży.")
    return [c for c in sale.corrections if c.deleted_at is None]
