"""Daty biznesowe, kwartały i strefa czasowa.

Daty sprzedaży/kosztów to zwykłe daty kalendarzowe (bez strefy).
Znaczniki techniczne (created_at itp.) trzymamy w UTC, a prezentujemy
w Europe/Warsaw po stronie interfejsu.
"""

from __future__ import annotations

import calendar
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

WARSAW = ZoneInfo("Europe/Warsaw")

QUARTER_LABELS = {1: "I kwartał", 2: "II kwartał", 3: "III kwartał", 4: "IV kwartał"}
MONTH_NAMES_PL = {
    1: "styczeń",
    2: "luty",
    3: "marzec",
    4: "kwiecień",
    5: "maj",
    6: "czerwiec",
    7: "lipiec",
    8: "sierpień",
    9: "wrzesień",
    10: "październik",
    11: "listopad",
    12: "grudzień",
}


def utcnow() -> datetime:
    """Aktualny czas UTC (świadomy strefy)."""
    return datetime.now(timezone.utc)


def now_local() -> datetime:
    """Aktualny czas lokalny użytkownika (Europe/Warsaw)."""
    return datetime.now(WARSAW)


def today_local() -> date:
    """Dzisiejsza data według strefy Europe/Warsaw."""
    return now_local().date()


def quarter_of(value: date) -> int:
    return (value.month - 1) // 3 + 1


def quarter_range(year: int, quarter: int) -> tuple[date, date]:
    if quarter not in (1, 2, 3, 4):
        raise ValueError("Kwartał musi mieścić się w zakresie 1-4")
    start_month = 3 * (quarter - 1) + 1
    end_month = start_month + 2
    last_day = calendar.monthrange(year, end_month)[1]
    return date(year, start_month, 1), date(year, end_month, last_day)


def month_range(year: int, month: int) -> tuple[date, date]:
    if month not in range(1, 13):
        raise ValueError("Miesiąc musi mieścić się w zakresie 1-12")
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def year_range(year: int) -> tuple[date, date]:
    return date(year, 1, 1), date(year, 12, 31)


def format_pl_date(value: date | None) -> str:
    """Format DD.MM.RRRR używany w dokumentach PDF i eksportach."""
    if value is None:
        return ""
    return value.strftime("%d.%m.%Y")


def format_pl_datetime(value: datetime | None) -> str:
    if value is None:
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(WARSAW).strftime("%d.%m.%Y %H:%M")
