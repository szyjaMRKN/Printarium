"""Sprzedaż i jej pozycje."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin
from app.models.enums import CustomerType, PaymentStatus


class Sale(Base, TimestampMixin, SoftDeleteMixin):
    """Jedna transakcja sprzedaży.

    Kwoty denormalizowane (accrued_revenue_gr, paid_amount_gr, payment_status)
    są przeliczane wyłącznie przez serwis sprzedaży — nigdy ręcznie z API.
    """

    __tablename__ = "sales"
    __table_args__ = (
        Index("ix_sales_sale_date_id", "sale_date", "id"),
        Index("ix_sales_channel_date", "sales_channel", "sale_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_number: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    sale_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)

    items_total_gr: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    discount_gr: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shipping_gr: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_gr: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    corrections_total_gr: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    accrued_revenue_gr: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)

    paid_amount_gr: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payment_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=PaymentStatus.UNPAID.value, index=True
    )
    first_payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_payment_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    payment_method: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    sales_channel: Mapped[str | None] = mapped_column(String(32), nullable=True)
    customer_type: Mapped[str] = mapped_column(String(8), nullable=False, default=CustomerType.B2C.value, index=True)

    customer_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    customer_nip: Mapped[str | None] = mapped_column(String(20), nullable=True)
    customer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    customer_address: Mapped[str | None] = mapped_column(Text, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    items: Mapped[list["SaleItem"]] = relationship(
        back_populates="sale", cascade="all, delete-orphan", order_by="SaleItem.position"
    )
    payments: Mapped[list["Payment"]] = relationship(  # noqa: F821
        back_populates="sale", cascade="all, delete-orphan"
    )
    corrections: Mapped[list["Correction"]] = relationship(  # noqa: F821
        back_populates="sale", cascade="all, delete-orphan"
    )

    @property
    def outstanding_gr(self) -> int:
        """Należność pozostała do zapłaty (nigdy ujemna)."""
        return max(self.accrued_revenue_gr - self.paid_amount_gr, 0)


class SaleItem(Base):
    __tablename__ = "sale_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    variant: Mapped[str | None] = mapped_column(String(120), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price_gr: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    line_total_gr: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    sale: Mapped[Sale] = relationship(back_populates="items")
