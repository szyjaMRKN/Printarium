"""Dane pomocnicze do rozliczenia PIT.

Program nie składa deklaracji — przygotowuje wyłącznie zestawienia.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.dates import MONTH_NAMES_PL, month_range, quarter_range, year_range
from app.services import reports_service

PIT_DISCLAIMER = (
    "Dane pomocnicze do rozliczenia działalności nierejestrowanej w PIT-36. "
    "Program nie zastępuje porady podatkowej ani oficjalnego systemu rozliczeń."
)


@dataclass
class PeriodSummary:
    label: str
    received_gr: int
    costs_gr: int
    income_gr: int
    accrued_gr: int


def _summary(session: Session, label: str, bounds) -> PeriodSummary:
    date_from, date_to = bounds
    received = reports_service.received_sum(session, date_from, date_to)
    costs = reports_service.costs_sum(session, date_from, date_to)
    return PeriodSummary(
        label=label,
        received_gr=received,
        costs_gr=costs,
        income_gr=received - costs,
        accrued_gr=reports_service.accrued_sum(session, date_from, date_to),
    )


def pit_summary(session: Session, year: int) -> dict:
    monthly = [_summary(session, MONTH_NAMES_PL[month], month_range(year, month)) for month in range(1, 13)]
    quarterly = [_summary(session, f"Q{quarter}", quarter_range(year, quarter)) for quarter in (1, 2, 3, 4)]
    yearly = _summary(session, str(year), year_range(year))
    return {
        "year": year,
        "disclaimer": PIT_DISCLAIMER,
        "monthly": [item.__dict__ for item in monthly],
        "quarterly": [item.__dict__ for item in quarterly],
        "yearly": yearly.__dict__,
    }
