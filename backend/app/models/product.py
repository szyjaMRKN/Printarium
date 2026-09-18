"""Baza produktów."""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin


class Product(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    sku: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    price_gr: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    production_cost_gr: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Miejsce na przyszłe rozszerzenia (numer partii, numer seryjny, wersja,
    # dokumentacja GPSR, instrukcja, informacje bezpieczeństwa) bez migracji schematu.
    attributes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
