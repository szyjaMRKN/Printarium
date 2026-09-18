"""Pulpit, limity działalności nierejestrowanej i PIT."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, db_session, get_current_context
from app.core.dates import today_local
from app.services import dashboard_service, limits_service, pit_service
from app.services.settings_service import SettingsService

router = APIRouter(tags=["pulpit"])


@router.get("/dashboard")
def dashboard(
    _: CurrentUser = Depends(get_current_context), session: Session = Depends(db_session)
) -> dict:
    data = dashboard_service.dashboard(session)
    session.commit()  # rok podatkowy mógł zostać utworzony przy pierwszym wejściu
    return data


@router.get("/limits")
def limits(
    year: int | None = Query(default=None, ge=2000, le=2100),
    _: CurrentUser = Depends(get_current_context),
    session: Session = Depends(db_session),
) -> dict:
    settings_service = SettingsService(session)
    year = year or settings_service.default_year()
    quarters = limits_service.year_summary(session, year)
    params = settings_service.fiscal_params(year)
    today = today_local()
    result = {
        "year": year,
        "parameters": {
            "minimum_wage_gr": params.minimum_wage_gr,
            "limit_multiplier_permille": params.limit_multiplier_permille,
            "quarterly_limit_gr": params.quarterly_limit_gr,
            "quarterly_limit_override_gr": params.quarterly_limit_override_gr,
        },
        "quarters": [
            {
                "year": item.year,
                "quarter": item.quarter,
                "label": item.label,
                "date_from": item.date_from,
                "date_to": item.date_to,
                "accrued_revenue_gr": item.accrued_revenue_gr,
                "limit_gr": item.limit_gr,
                "usage_percent": float(item.usage_percent),
                "remaining_gr": item.remaining_gr,
                "status": item.status,
                "message": item.message,
                "sales_count": item.sales_count,
                "exceedance": (
                    {
                        "exceeded_on": item.exceedance.exceeded_on,
                        "sale_id": item.exceedance.sale_id,
                        "sale_document_number": item.exceedance.sale_document_number,
                        "exceeded_by_gr": item.exceedance.exceeded_by_gr,
                        "cumulative_gr": item.exceedance.cumulative_gr,
                    }
                    if item.exceedance
                    else None
                ),
            }
            for item in quarters
        ],
        "counters": {
            "ksef": dashboard_service.counter_dict(
                limits_service.ksef_monthly_counter(session, year, today.month if today.year == year else 12)
            ),
            "cash_register": dashboard_service.counter_dict(
                limits_service.cash_register_counter(session, year)
            ),
        },
    }
    session.commit()
    return result


@router.get("/pit")
def pit(
    year: int | None = Query(default=None, ge=2000, le=2100),
    _: CurrentUser = Depends(get_current_context),
    session: Session = Depends(db_session),
) -> dict:
    year = year or SettingsService(session).default_year()
    return pit_service.pit_summary(session, year)
