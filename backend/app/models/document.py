"""Dokumenty sprzedaży: rachunki i faktury bez VAT."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin
from app.models.enums import DocumentType, KsefStatus


class SalesDocument(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "sales_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_type: Mapped[str] = mapped_column(String(32), nullable=False, default=DocumentType.RECEIPT.value)
    number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    number_seq: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    number_month: Mapped[int] = mapped_column(Integer, nullable=False)
    number_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    sale_id: Mapped[int | None] = mapped_column(ForeignKey("sales.id", ondelete="SET NULL"), nullable=True, index=True)

    issue_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    sale_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    seller_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    buyer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    buyer_nip: Mapped[str | None] = mapped_column(String(20), nullable=True)
    buyer_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    buyer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_type: Mapped[str] = mapped_column(String(8), nullable=False, default="b2c")

    items_snapshot: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    total_gr: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payment_method: Mapped[str | None] = mapped_column(String(32), nullable=True)
    paid_note: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    ksef_status: Mapped[str] = mapped_column(String(32), nullable=False, default=KsefStatus.NOT_APPLICABLE.value)
    ksef_number: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    sale: Mapped["Sale | None"] = relationship()  # noqa: F821
