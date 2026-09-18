from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import PaymentMethod


class CostCategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    is_active: bool = True
    sort_order: int = Field(default=100, ge=0, le=9999)


class CostCategoryCreate(CostCategoryBase):
    pass


class CostCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    is_active: bool | None = None
    sort_order: int | None = Field(default=None, ge=0, le=9999)


class CostCategoryOut(CostCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str


class CostBase(BaseModel):
    cost_date: date
    name: str = Field(min_length=1, max_length=200)
    category_id: int | None = None
    vendor: str | None = Field(default=None, max_length=200)
    invoice_number: str | None = Field(default=None, max_length=80)
    amount_gr: int = Field(ge=0, le=1_000_000_000)
    payment_method: PaymentMethod | None = None
    description: str | None = Field(default=None, max_length=2000)
    attachment_id: int | None = None

    @field_validator("name", "vendor", "invoice_number")
    @classmethod
    def _strip(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class CostCreate(CostBase):
    pass


class CostUpdate(CostBase):
    pass


class CostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cost_date: date
    name: str
    category_id: int | None
    category_name: str | None = None
    vendor: str | None
    invoice_number: str | None
    amount_gr: int
    payment_method: str | None
    description: str | None
    attachment_id: int | None
    attachment_name: str | None = None
    created_at: datetime
    updated_at: datetime


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_name: str
    content_type: str
    size_bytes: int
    created_at: datetime
