"""Słowniki dla interfejsu (etykiety po polsku)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, get_current_context
from app.core.version import APP_NAME, APP_VERSION
from app.models.enums import (
    CorrectionType,
    CustomerType,
    DocumentType,
    KsefStatus,
    PaymentMethod,
    PaymentStatus,
    SalesChannel,
    UserRole,
    label,
)
from app.services.reports_service import AVAILABLE_REPORTS

router = APIRouter(prefix="/meta", tags=["slowniki"])


def _options(enum_cls) -> list[dict[str, str]]:
    return [{"value": item.value, "label": label(item.value)} for item in enum_cls]


@router.get("/options")
def options(_: CurrentUser = Depends(get_current_context)) -> dict:
    return {
        "app": {"name": APP_NAME, "version": APP_VERSION},
        "payment_status": _options(PaymentStatus),
        "payment_method": _options(PaymentMethod),
        "sales_channel": _options(SalesChannel),
        "customer_type": _options(CustomerType),
        "correction_type": _options(CorrectionType),
        "document_type": _options(DocumentType),
        "ksef_status": _options(KsefStatus),
        "user_role": _options(UserRole),
        "reports": [{"value": key, "label": title} for key, title in AVAILABLE_REPORTS],
    }
