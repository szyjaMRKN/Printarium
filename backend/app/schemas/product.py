from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    sku: str | None = Field(default=None, max_length=64)
    model: str | None = Field(default=None, max_length=120)
    category: str | None = Field(default=None, max_length=120)
    price_gr: int = Field(default=0, ge=0, le=1_000_000_000)
    production_cost_gr: int = Field(default=0, ge=0, le=1_000_000_000)
    is_active: bool = True
    description: str | None = Field(default=None, max_length=4000)
    # Miejsce na przyszłe pola (partia, numer seryjny, GPSR, instrukcje).
    attributes: dict[str, Any] | None = None

    @field_validator("name", "sku", "model", "category")
    @classmethod
    def _strip(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    pass


class ProductOut(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
