"""Limity działalności nierejestrowanej oraz progi pomocnicze (KSeF, kasa fiskalna).

Wszystkie wartości progów pochodzą z bazy (tabela fiscal_years) — w kodzie nie
ma żadnej zaszytej kwoty limitu.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dates import QUARTER_LABELS, month_range, quarter_of, quarter_range, today_local, year_range
from app.core.money import percent_of
from app.models.document import SalesDocument
from app.models.enums import CustomerType
from app.models.sale import Sale
from app.services.settings_service import SettingsService

STATUS_NORMAL = "normalny"
STATUS_WARNING = "ostrzezenie"
STATUS_STRONG_WARNING = "mocne_ostrzezenie"
STATUS_EXCEEDED = "przekroczony"

WARNING_MESSAGE = "UWAGA: Zbliżasz się do limitu działalności nierejestrowanej."
EXCEEDED_MESSAGE = (
    "PRZEKROCZONO LIMIT DZIAŁALNOŚCI NIEREJESTROWANEJ. "
    "Sprawdź obowiązek rejestracji działalności w CEIDG. "
    "Termin na rejestrację wynosi co do zasady 7 dni od dnia przekroczenia limitu."
)


@dataclass
class ExceedanceInfo:
    exceeded_on: date
    sale_id: int
    sale_document_number: str | None
    exceeded_by_gr: int
    cumulative_gr: int


@dataclass
class QuarterSummary:
    year: int
    quarter: int
    label: str
    date_from: date
    date_to: date
    accrued_revenue_gr: int
    limit_gr: int
    usage_percent: Decimal
    remaining_gr: int
    status: str
    sales_count: int
    message: str | None
    exceedance: ExceedanceInfo | None


def resolve_status(percent: Decimal, warning_percent: int, strong_percent: int) -> str:
    if percent >= 100:
        return STATUS_EXCEEDED
    if percent >= strong_percent:
        return STATUS_STRONG_WARNING
    if percent >= warning_percent:
        return STATUS_WARNING
    return STATUS_NORMAL


def status_message(status: str) -> str | None:
    if status == STATUS_EXCEEDED:
        return EXCEEDED_MESSAGE
    if status in (STATUS_STRONG_WARNING,):
        return WARNING_MESSAGE
    return None


def accrued_revenue_between(session: Session, date_from: date, date_to: date, **filters) -> int:
    stmt = select(func.coalesce(func.sum(Sale.accrued_revenue_gr), 0)).where(
        Sale.deleted_at.is_(None),
        Sale.sale_date >= date_from,
        Sale.sale_date <= date_to,
    )
    customer_type = filters.get("customer_type")
    if customer_type:
        stmt = stmt.where(Sale.customer_type == customer_type)
    return int(session.execute(stmt).scalar_one())


def find_exceedance(session: Session, date_from: date, date_to: date, limit_gr: int) -> ExceedanceInfo | None:
    """Znajduje sprzedaż, która przekroczyła limit w danym okresie."""
    if limit_gr <= 0:
        return None
    rows = session.execute(
        select(Sale.id, Sale.document_number, Sale.sale_date, Sale.accrued_revenue_gr)
        .where(Sale.deleted_at.is_(None), Sale.sale_date >= date_from, Sale.sale_date <= date_to)
        .order_by(Sale.sale_date.asc(), Sale.id.asc())
    ).all()
    cumulative = 0
    for sale_id, number, sale_date, accrued in rows:
        cumulative += accrued
        if cumulative > limit_gr:
            return ExceedanceInfo(
                exceeded_on=sale_date,
                sale_id=sale_id,
                sale_document_number=number,
                exceeded_by_gr=cumulative - limit_gr,
                cumulative_gr=cumulative,
            )
    return None


def quarter_summary(session: Session, year: int, quarter: int) -> QuarterSummary:
    settings_service = SettingsService(session)
    params = settings_service.fiscal_params(year)
    warning_percent = settings_service.get_int("fiscal.warning_percent")
    strong_percent = settings_service.get_int("fiscal.strong_warning_percent")

    date_from, date_to = quarter_range(year, quarter)
    accrued = accrued_revenue_between(session, date_from, date_to)
    sales_count = int(
        session.execute(
            select(func.count(Sale.id)).where(
                Sale.deleted_at.is_(None), Sale.sale_date >= date_from, Sale.sale_date <= date_to
            )
        ).scalar_one()
    )
    limit_gr = params.quarterly_limit_gr
    percent = percent_of(accrued, limit_gr)
    status = resolve_status(percent, warning_percent, strong_percent)
    exceedance = find_exceedance(session, date_from, date_to, limit_gr) if status == STATUS_EXCEEDED else None

    return QuarterSummary(
        year=year,
        quarter=quarter,
        label=QUARTER_LABELS[quarter],
        date_from=date_from,
        date_to=date_to,
        accrued_revenue_gr=accrued,
        limit_gr=limit_gr,
        usage_percent=percent,
        remaining_gr=max(limit_gr - accrued, 0),
        status=status,
        sales_count=sales_count,
        message=status_message(status),
        exceedance=exceedance,
    )


def year_summary(session: Session, year: int) -> list[QuarterSummary]:
    return [quarter_summary(session, year, quarter) for quarter in (1, 2, 3, 4)]


def current_quarter_summary(session: Session, today: date | None = None) -> QuarterSummary:
    today = today or today_local()
    return quarter_summary(session, today.year, quarter_of(today))


@dataclass
class ThresholdCounter:
    """Licznik pomocniczy z progiem konfigurowalnym w ustawieniach."""

    label: str
    period_label: str
    value_gr: int
    threshold_gr: int
    usage_percent: Decimal
    status: str
    message: str | None


def ksef_monthly_counter(session: Session, year: int, month: int) -> ThresholdCounter:
    """Miesięczna wartość sprzedaży udokumentowanej fakturami (pomocniczo dla KSeF)."""
    settings_service = SettingsService(session)
    params = settings_service.fiscal_params(year)
    date_from, date_to = month_range(year, month)
    value = int(
        session.execute(
            select(func.coalesce(func.sum(SalesDocument.total_gr), 0)).where(
                SalesDocument.deleted_at.is_(None),
                SalesDocument.issue_date >= date_from,
                SalesDocument.issue_date <= date_to,
            )
        ).scalar_one()
    )
    threshold = params.ksef_monthly_threshold_gr
    percent = percent_of(value, threshold)
    status = resolve_status(percent, 75, 90)
    message = None
    if status in (STATUS_STRONG_WARNING, STATUS_EXCEEDED):
        message = (
            "Wartość sprzedaży udokumentowanej fakturami zbliża się do progu lub go przekroczyła. "
            "Zweryfikuj obowiązek korzystania z KSeF."
        )
    return ThresholdCounter(
        label="Sprzedaż udokumentowana fakturami (KSeF)",
        period_label=f"{month:02d}.{year}",
        value_gr=value,
        threshold_gr=threshold,
        usage_percent=percent,
        status=status,
        message=message,
    )


def cash_register_counter(session: Session, year: int) -> ThresholdCounter:
    """Roczna sprzedaż B2C — licznik pomocniczy dla zwolnienia z kasy fiskalnej."""
    settings_service = SettingsService(session)
    params = settings_service.fiscal_params(year)
    date_from, date_to = year_range(year)
    value = accrued_revenue_between(session, date_from, date_to, customer_type=CustomerType.B2C.value)
    threshold = params.cash_register_yearly_threshold_gr
    percent = percent_of(value, threshold)
    status = resolve_status(percent, 75, 90)
    message = None
    if status in (STATUS_STRONG_WARNING, STATUS_EXCEEDED):
        message = (
            "Zbliżasz się do limitu sprzedaży, który może mieć znaczenie dla obowiązku stosowania "
            "kasy fiskalnej. Zweryfikuj możliwość korzystania ze zwolnienia."
        )
    return ThresholdCounter(
        label="Sprzedaż B2C (kasa fiskalna)",
        period_label=str(year),
        value_gr=value,
        threshold_gr=threshold,
        usage_percent=percent,
        status=status,
        message=message,
    )
