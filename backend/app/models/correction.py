"""Korekty sprzedaży — zwroty, rabaty po sprzedaży, anulowania."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin


class Correction(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "corrections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    correction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    correction_type: Mapped[str] = mapped_column(String(32), nullable=False)
    previous_value_gr: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_value_gr: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Kwota korekty przychodu należnego (ujemna = obniżenie przychodu).
    amount_gr: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    refund_amount_gr: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    sale: Mapped["Sale"] = relationship(back_populates="corrections")  # noqa: F821
