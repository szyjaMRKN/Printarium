"""Ustawienia aplikacji i parametry lat podatkowych.

Wszystkie wartości, które mogą się zmienić w przyszłości (limity, progi,
mnożniki), siedzą tutaj — nie w kodzie liczącym.
"""

from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Setting(Base, TimestampMixin):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_type: Mapped[str] = mapped_column(String(16), nullable=False, default="string")


class FiscalYear(Base, TimestampMixin):
    """Parametry roku podatkowego — limit działalności nierejestrowanej i progi."""

    __tablename__ = "fiscal_years"

    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    minimum_wage_gr: Mapped[int] = mapped_column(Integer, nullable=False)
    # Mnożnik w promilach: 2250 = 225% minimalnego wynagrodzenia.
    limit_multiplier_permille: Mapped[int] = mapped_column(Integer, nullable=False, default=2250)
    quarterly_limit_override_gr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ksef_monthly_threshold_gr: Mapped[int] = mapped_column(Integer, nullable=False, default=1_000_000)
    cash_register_yearly_threshold_gr: Mapped[int] = mapped_column(Integer, nullable=False, default=2_000_000)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
