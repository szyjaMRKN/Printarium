"""Schematy sprzedaży, płatności i korekt. Kwoty zawsze w groszach (int)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import (
    CorrectionType,
    CustomerType,
    PaymentMethod,
    PaymentStatus,
    SalesChannel,
)

MAX_AMOUNT_GR = 1_000_000_000  # 10 mln zł — twardy bezpiecznik walidacji


class SaleItemIn(BaseModel):
    product_id: int | None = None
    name: str = Field(min_length=1, max_length=200)
    variant: str | None = Field(default=None, max_length=120)
    quantity: int = Field(ge=1, le=1_000_000)
    unit_price_gr: int = Field(ge=0, le=MAX_AMOUNT_GR)

    @field_validator("name", "variant")
    @classmethod
    def _strip(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class SaleItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int | None
    position: int
    name: str
    variant: str | None
    quantity: int
    unit_price_gr: int
    line_total_gr: int


class InitialPaymentIn(BaseModel):
    amount_gr: int = Field(gt=0, le=MAX_AMOUNT_GR)
    payment_date: date
    method: PaymentMethod = PaymentMethod.TRANSFER
    description: str | None = Field(default=None, max_length=500)


class SaleBase(BaseModel):
    document_number: str | None = Field(default=None, max_length=64)
    sale_date: date
    description: str | None = Field(default=None, max_length=300)
    discount_gr: int = Field(default=0, ge=0, le=MAX_AMOUNT_GR)
    shipping_gr: int = Field(default=0, ge=0, le=MAX_AMOUNT_GR)
    payment_method: PaymentMethod | None = None
    sales_channel: SalesChannel | None = None
    customer_type: CustomerType = CustomerType.B2C
    customer_name: str | None = Field(default=None, max_length=200)
    customer_nip: str | None = Field(default=None, max_length=20)
    customer_email: str | None = Field(default=None, max_length=255)
    customer_phone: str | None = Field(default=None, max_length=40)
    customer_address: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("document_number", "customer_name", "customer_nip", "description")
    @classmethod
    def _strip(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class SaleCreate(SaleBase):
    items: list[SaleItemIn] = Field(min_length=1, max_length=200)
    initial_payment: InitialPaymentIn | None = None


class SaleUpdate(SaleBase):
    items: list[SaleItemIn] = Field(min_length=1, max_length=200)


class PaymentCreate(BaseModel):
    payment_date: date
    amount_gr: int = Field(le=MAX_AMOUNT_GR, ge=-MAX_AMOUNT_GR)
    method: PaymentMethod = PaymentMethod.TRANSFER
    description: str | None = Field(default=None, max_length=500)

    @field_validator("amount_gr")
    @classmethod
    def _not_zero(cls, value: int) -> int:
        if value == 0:
            raise ValueError("Kwota płatności nie może wynosić 0.")
        return value


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sale_id: int
    payment_date: date
    amount_gr: int
    method: str
    description: str | None
    correction_id: int | None
    created_at: datetime


class CorrectionCreate(BaseModel):
    correction_date: date
    correction_type: CorrectionType
    # Kwota korekty podawana jako wartość dodatnia (obniżenie przychodu) —
    # dla korekty wartości przekazujemy nową wartość sprzedaży w new_value_gr.
    amount_gr: int | None = Field(default=None, ge=0, le=MAX_AMOUNT_GR)
    new_value_gr: int | None = Field(default=None, ge=0, le=MAX_AMOUNT_GR)
    refund_amount_gr: int = Field(default=0, ge=0, le=MAX_AMOUNT_GR)
    refund_method: PaymentMethod | None = None
    reason: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class CorrectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sale_id: int
    correction_date: date
    correction_type: str
    previous_value_gr: int
    new_value_gr: int
    amount_gr: int
    refund_amount_gr: int
    reason: str | None
    description: str | None
    created_by_id: int | None
    created_at: datetime


class SaleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_number: str | None
    sale_date: date
    description: str | None
    items_total_gr: int
    discount_gr: int
    shipping_gr: int
    total_gr: int
    corrections_total_gr: int
    accrued_revenue_gr: int
    paid_amount_gr: int
    outstanding_gr: int
    payment_status: PaymentStatus
    first_payment_date: date | None
    last_payment_date: date | None
    payment_method: str | None
    sales_channel: str | None
    customer_type: str
    customer_name: str | None
    customer_nip: str | None
    customer_email: str | None
    customer_phone: str | None
    customer_address: str | None
    notes: str | None
    is_cancelled: bool
    created_at: datetime
    updated_at: datetime
    items: list[SaleItemOut] = []
    payments: list[PaymentOut] = []
    corrections: list[CorrectionOut] = []


class SaleListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_number: str | None
    sale_date: date
    description: str | None
    total_gr: int
    corrections_total_gr: int
    accrued_revenue_gr: int
    paid_amount_gr: int
    outstanding_gr: int
    payment_status: PaymentStatus
    payment_method: str | None
    sales_channel: str | None
    customer_type: str
    customer_name: str | None
    last_payment_date: date | None
    is_cancelled: bool


class RegistryRow(BaseModel):
    """Wiersz ewidencji sprzedaży z przychodem narastająco."""

    lp: int
    sale_id: int
    sale_date: date
    document_number: str | None
    description: str | None
    total_gr: int
    corrections_total_gr: int
    accrued_revenue_gr: int
    cumulative_gr: int
    payment_status: PaymentStatus
    paid_amount_gr: int


class DailyRegistryRow(BaseModel):
    lp: int
    day: date
    sales_count: int
    total_gr: int
    cumulative_gr: int
