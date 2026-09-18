"""Dokumenty sprzedaży: rachunki i faktury bez VAT + numeracja + KSeF."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.dates import utcnow
from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.document import SalesDocument
from app.models.enums import AuditAction, CustomerType, DocumentType, KsefStatus
from app.models.user import User
from app.repositories import sales_repo
from app.schemas.document import DocumentCreate, DocumentItemIn, DocumentUpdate
from app.services import audit_service
from app.services.settings_service import SettingsService


def format_number(pattern: str, seq: int, issue_date: date) -> str:
    return (
        pattern.replace("{nr}", str(seq))
        .replace("{mm}", f"{issue_date.month:02d}")
        .replace("{m}", str(issue_date.month))
        .replace("{rrrr}", str(issue_date.year))
        .replace("{rr}", f"{issue_date.year % 100:02d}")
    )


def next_number(session: Session, issue_date: date) -> tuple[str, int]:
    settings_service = SettingsService(session)
    pattern = settings_service.get_str("invoicing.number_format") or "{nr}/{mm}/{rrrr}"
    reset_period = settings_service.get_str("invoicing.reset_period") or "month"

    stmt = select(func.coalesce(func.max(SalesDocument.number_seq), 0)).where(
        SalesDocument.number_year == issue_date.year
    )
    if reset_period == "month":
        stmt = stmt.where(SalesDocument.number_month == issue_date.month)
    seq = int(session.execute(stmt).scalar_one()) + 1

    number = format_number(pattern, seq, issue_date)
    while session.execute(
        select(SalesDocument.id).where(SalesDocument.number == number).limit(1)
    ).scalar_one_or_none() is not None:
        seq += 1
        number = format_number(pattern, seq, issue_date)
    return number, seq


def query(
    *,
    year: int | None = None,
    document_type: str | None = None,
    ksef_status: str | None = None,
    search: str | None = None,
) -> Select:
    stmt = (
        select(SalesDocument)
        .where(SalesDocument.deleted_at.is_(None))
        .order_by(SalesDocument.issue_date.desc(), SalesDocument.id.desc())
    )
    if year:
        stmt = stmt.where(SalesDocument.number_year == year)
    if document_type:
        stmt = stmt.where(SalesDocument.document_type == document_type)
    if ksef_status:
        stmt = stmt.where(SalesDocument.ksef_status == ksef_status)
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            (SalesDocument.number.ilike(pattern))
            | (SalesDocument.buyer_name.ilike(pattern))
            | (SalesDocument.buyer_nip.ilike(pattern))
        )
    return stmt


def get_document(session: Session, document_id: int) -> SalesDocument:
    document = session.get(SalesDocument, document_id)
    if document is None or document.deleted_at is not None:
        raise NotFoundError("Nie znaleziono dokumentu.")
    return document


def _items_from_sale(sale) -> list[dict]:
    items = [
        {
            "name": item.name + (f" ({item.variant})" if item.variant else ""),
            "quantity": item.quantity,
            "unit": "szt.",
            "unit_price_gr": item.unit_price_gr,
            "total_gr": item.line_total_gr,
        }
        for item in sale.items
    ]
    if sale.discount_gr:
        items.append(
            {"name": "Rabat", "quantity": 1, "unit": "szt.", "unit_price_gr": -sale.discount_gr,
             "total_gr": -sale.discount_gr}
        )
    if sale.shipping_gr:
        items.append(
            {"name": "Wysyłka", "quantity": 1, "unit": "szt.", "unit_price_gr": sale.shipping_gr,
             "total_gr": sale.shipping_gr}
        )
    return items


def _items_from_input(items: list[DocumentItemIn]) -> list[dict]:
    return [
        {
            "name": item.name,
            "quantity": item.quantity,
            "unit": item.unit,
            "unit_price_gr": item.unit_price_gr,
            "total_gr": item.quantity * item.unit_price_gr,
        }
        for item in items
    ]


def create_document(
    session: Session, data: DocumentCreate, user: User | None, *, ip: str | None = None
) -> SalesDocument:
    settings_service = SettingsService(session)
    seller = settings_service.seller_data()
    if not seller.get("name"):
        raise ValidationError(
            "Uzupełnij dane sprzedawcy w ustawieniach przed wystawieniem dokumentu."
        )

    sale = None
    if data.sale_id is not None:
        sale = sales_repo.get_sale(session, data.sale_id)
        if sale is None:
            raise NotFoundError("Nie znaleziono sprzedaży powiązanej z dokumentem.")

    items = _items_from_input(data.items) if data.items else (_items_from_sale(sale) if sale else [])
    if not items:
        raise ValidationError("Dokument musi zawierać co najmniej jedną pozycję.")

    total = sum(int(item["total_gr"]) for item in items)
    issue_date = data.issue_date
    sale_date = data.sale_date or (sale.sale_date if sale else issue_date)

    if data.number_override:
        number = data.number_override
        if session.execute(
            select(SalesDocument.id).where(SalesDocument.number == number).limit(1)
        ).scalar_one_or_none() is not None:
            raise ConflictError(f"Dokument o numerze {number} już istnieje.")
        seq = 0
    else:
        number, seq = next_number(session, issue_date)

    due_date = data.due_date
    if due_date is None:
        days = settings_service.get_int("invoicing.default_payment_days")
        due_date = issue_date + timedelta(days=days) if days > 0 else None

    ksef_status = data.ksef_status
    if data.customer_type is CustomerType.B2C and ksef_status is KsefStatus.NOT_APPLICABLE:
        ksef_status = KsefStatus.NOT_APPLICABLE

    document = SalesDocument(
        document_type=data.document_type.value,
        number=number,
        number_seq=seq,
        number_month=issue_date.month,
        number_year=issue_date.year,
        sale_id=sale.id if sale else None,
        issue_date=issue_date,
        sale_date=sale_date,
        due_date=due_date,
        seller_snapshot=seller,
        buyer_name=data.buyer_name or (sale.customer_name if sale else ""),
        buyer_nip=data.buyer_nip or (sale.customer_nip if sale else None),
        buyer_address=data.buyer_address or (sale.customer_address if sale else None),
        buyer_email=data.buyer_email or (sale.customer_email if sale else None),
        customer_type=data.customer_type.value,
        items_snapshot=items,
        total_gr=total,
        payment_method=(data.payment_method.value if data.payment_method else (sale.payment_method if sale else None)),
        paid_note=data.paid_note,
        notes=data.notes,
        ksef_status=ksef_status.value,
        ksef_number=data.ksef_number,
        created_by_id=user.id if user else None,
    )
    session.add(document)
    session.flush()
    audit_service.record(
        session,
        AuditAction.DOCUMENT_CREATE,
        user=user,
        entity_type="document",
        entity_id=document.id,
        ip_address=ip,
        description=f"Wystawiono dokument {document.number} na kwotę {document.total_gr} gr.",
    )
    return document


def update_document(
    session: Session, document_id: int, data: DocumentUpdate, user: User | None, *, ip: str | None = None
) -> SalesDocument:
    document = get_document(session, document_id)
    payload = data.model_dump(exclude_unset=True)
    for key, value in payload.items():
        if key in ("ksef_status",) and value is not None:
            document.ksef_status = value.value if hasattr(value, "value") else value
        elif key == "payment_method" and value is not None:
            document.payment_method = value.value if hasattr(value, "value") else value
        elif value is not None or key in ("due_date", "ksef_number", "notes", "paid_note"):
            setattr(document, key, value)
    session.flush()
    audit_service.record(
        session,
        AuditAction.DOCUMENT_UPDATE,
        user=user,
        entity_type="document",
        entity_id=document.id,
        ip_address=ip,
        description=f"Zmieniono dokument {document.number}.",
    )
    return document


def soft_delete_document(
    session: Session, document_id: int, user: User | None, *, ip: str | None = None
) -> SalesDocument:
    document = get_document(session, document_id)
    document.deleted_at = utcnow()
    session.flush()
    audit_service.record(
        session,
        AuditAction.DOCUMENT_DELETE,
        user=user,
        entity_type="document",
        entity_id=document.id,
        ip_address=ip,
        description=f"Usunięto (miękko) dokument {document.number}.",
    )
    return document


def document_types() -> list[tuple[str, str]]:
    return [(item.value, item.name) for item in DocumentType]
