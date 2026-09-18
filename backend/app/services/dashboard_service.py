"""Dane dla pulpitu."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.dates import month_range, quarter_of, quarter_range, today_local, year_range
from app.services import limits_service, reports_service


def _avg(total: int, count: int) -> int:
    return int(round(total / count)) if count else 0


def dashboard(session: Session, today: date | None = None) -> dict:
    today = today or today_local()
    year = today.year
    quarter = quarter_of(today)

    month_from, month_to = month_range(year, today.month)
    quarter_from, quarter_to = quarter_range(year, quarter)
    year_from, year_to = year_range(year)

    quarter_limit = limits_service.quarter_summary(session, year, quarter)

    accrued_today = reports_service.accrued_sum(session, today, today)
    accrued_month = reports_service.accrued_sum(session, month_from, month_to)
    accrued_quarter = quarter_limit.accrued_revenue_gr
    accrued_year = reports_service.accrued_sum(session, year_from, year_to)

    received_month = reports_service.received_sum(session, month_from, month_to)
    received_quarter = reports_service.received_sum(session, quarter_from, quarter_to)
    received_year = reports_service.received_sum(session, year_from, year_to)

    costs_month = reports_service.costs_sum(session, month_from, month_to)
    costs_year = reports_service.costs_sum(session, year_from, year_to)

    orders_today = reports_service.sales_count(session, today, today)
    orders_month = reports_service.sales_count(session, month_from, month_to)
    orders_year = reports_service.sales_count(session, year_from, year_to)

    return {
        "today": today,
        "year": year,
        "quarter": quarter,
        "limit": {
            "year": quarter_limit.year,
            "quarter": quarter_limit.quarter,
            "label": quarter_limit.label,
            "date_from": quarter_limit.date_from,
            "date_to": quarter_limit.date_to,
            "accrued_revenue_gr": quarter_limit.accrued_revenue_gr,
            "limit_gr": quarter_limit.limit_gr,
            "usage_percent": float(quarter_limit.usage_percent),
            "remaining_gr": quarter_limit.remaining_gr,
            "status": quarter_limit.status,
            "message": quarter_limit.message,
            "sales_count": quarter_limit.sales_count,
            "exceedance": (
                {
                    "exceeded_on": quarter_limit.exceedance.exceeded_on,
                    "sale_id": quarter_limit.exceedance.sale_id,
                    "sale_document_number": quarter_limit.exceedance.sale_document_number,
                    "exceeded_by_gr": quarter_limit.exceedance.exceeded_by_gr,
                    "cumulative_gr": quarter_limit.exceedance.cumulative_gr,
                }
                if quarter_limit.exceedance
                else None
            ),
        },
        "metrics": {
            "accrued_today_gr": accrued_today,
            "accrued_month_gr": accrued_month,
            "accrued_quarter_gr": accrued_quarter,
            "accrued_year_gr": accrued_year,
            "received_month_gr": received_month,
            "received_quarter_gr": received_quarter,
            "received_year_gr": received_year,
            "outstanding_gr": reports_service.outstanding_total(session),
            "costs_month_gr": costs_month,
            "costs_year_gr": costs_year,
            "income_year_gr": received_year - costs_year,
            "income_month_gr": received_month - costs_month,
            "orders_today": orders_today,
            "orders_month": orders_month,
            "orders_year": orders_year,
            "average_order_month_gr": _avg(accrued_month, orders_month),
            "average_order_year_gr": _avg(accrued_year, orders_year),
        },
        "charts": {
            "last_30_days": reports_service.daily_series(session, today - timedelta(days=29), today),
            "monthly": reports_service.monthly_series(session, year),
            "by_channel": reports_service.by_channel(session, year_from, year_to),
            "by_product": reports_service.by_product(session, year_from, year_to, limit=8),
            "by_customer_type": reports_service.by_customer_type(session, year_from, year_to),
            "costs_by_category": reports_service.costs_by_category(session, year_from, year_to),
        },
        "counters": {
            "ksef": counter_dict(limits_service.ksef_monthly_counter(session, year, today.month)),
            "cash_register": counter_dict(limits_service.cash_register_counter(session, year)),
        },
    }


def counter_dict(counter) -> dict:
    return {
        "label": counter.label,
        "period_label": counter.period_label,
        "value_gr": counter.value_gr,
        "threshold_gr": counter.threshold_gr,
        "usage_percent": float(counter.usage_percent),
        "status": counter.status,
        "message": counter.message,
    }
