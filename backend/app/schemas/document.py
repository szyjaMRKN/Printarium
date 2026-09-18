from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import CustomerType, DocumentType, KsefStatus, PaymentMethod


class DocumentItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    quantity: int = Field(ge=1, le=1_000_000)
    unit_price_gr: int = Field(ge=0, le=1_000_000_000)
    unit: str = Field(default="szt.", max_length=20)


class DocumentCreate(BaseModel):
    document_type: DocumentType = DocumentType.RECEIPT
    sale_id: int | None = None
    issue_date: date
    sale_date: date | None = None
    due_date: date | None = None
    buyer_name: str = Field(min_length=1, max_length=200)
    buyer_nip: str | None = Field(default=None, max_length=20)
    buyer_address: str | None = Field(default=None, max_length=1000)
    buyer_email: str | None = Field(default=None, max_length=255)
    customer_type: CustomerType = CustomerType.B2C
    items: list[DocumentItemIn] = Field(default_factory=list, max_length=100)
    payment_method: PaymentMethod | None = None
    paid_note: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)
    ksef_status: KsefStatus = KsefStatus.NOT_APPLICABLE
    ksef_number: str | None = Field(default=None, max_length=64)
    number_override: str | None = Field(default=None, max_length=64)

    @field_validator("buyer_name")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()


class DocumentUpdate(BaseModel):
    buyer_name: str | None = Field(default=None, min_length=1, max_length=200)
    buyer_nip: str | None = Field(default=None, max_length=20)
    buyer_address: str | None = Field(default=None, max_length=1000)
    buyer_email: str | None = Field(default=None, max_length=255)
    due_date: date | None = None
    payment_method: PaymentMethod | None = None
    paid_note: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)
    ksef_status: KsefStatus | None = None
    ksef_number: str | None = Field(default=None, max_length=64)


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_type: str
    number: str
    sale_id: int | None
    issue_date: date
    sale_date: date
    due_date: date | None
    buyer_name: str
    buyer_nip: str | None
    buyer_address: str | None
    buyer_email: str | None
    customer_type: str
    items_snapshot: list
    seller_snapshot: dict
    total_gr: int
    payment_method: str | None
    paid_note: str | None
    notes: str | None
    ksef_status: str
    ksef_number: str | None
    created_at: datetime
