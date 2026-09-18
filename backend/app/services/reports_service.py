"""Agregacje i zestawienia.

Grupowanie po dniach/miesiącach robimy w Pythonie, a nie funkcjami SQLite
(strftime), żeby przejście na PostgreSQL nie wymagało przepisywania zapytań.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dates import MONTH_NAMES_PL, month_range, quarter_of, quarter_range, today_local, year_range
from app.models.cost import Cost, CostCategory
from app.models.enums import CustomerType, PaymentStatus
from app.models.payment import Payment
from app.models.sale import Sale, SaleItem
from app.repositories.sales_repo import SaleFilters, base_query

MAX_REGISTRY_ROWS = 20000


# --- proste sumy ---


def accrued_sum(
    session: Session,
    date_from: date,
    date_to: date,
    *,
    customer_type: str | None = None,
    sales_channel: str | None = None,
) -> int:
    stmt = select(func.coalesce(func.sum(Sale.accrued_revenue_gr), 0)).where(
        Sale.deleted_at.is_(None), Sale.sale_date >= date_from, Sale.sale_date <= date_to
    )
    if customer_type:
        stmt = stmt.where(Sale.customer_type == customer_type)
    if sales_channel:
        stmt = stmt.where(Sale.sales_channel == sales_channel)
    return int(session.execute(stmt).scalar_one())


def received_sum(session: Session, date_from: date, date_to: date) -> int:
    """Przychód faktycznie otrzymany (wpłaty minus zwroty pieniędzy)."""
    stmt = (
        select(func.coalesce(func.sum(Payment.amount_gr), 0))
        .join(Sale, Sale.id == Payment.sale_id)
        .where(
            Payment.deleted_at.is_(None),
            Sale.deleted_at.is_(None),
            Payment.payment_date >= date_from,
            Payment.payment_date <= date_to,
        )
    )
    return int(session.execute(stmt).scalar_one())


def costs_sum(session: Session, date_from: date, date_to: date) -> int:
    stmt = select(func.coalesce(func.sum(Cost.amount_gr), 0)).where(
        Cost.deleted_at.is_(None), Cost.cost_date >= date_from, Cost.cost_date <= date_to
    )
    return int(session.execute(stmt).scalar_one())


def sales_count(session: Session, date_from: date, date_to: date) -> int:
    stmt = select(func.count(Sale.id)).where(
        Sale.deleted_at.is_(None),
        Sale.sale_date >= date_from,
        Sale.sale_date <= date_to,
        Sale.is_cancelled.is_(False),
    )
    return int(session.execute(stmt).scalar_one())


def outstanding_total(session: Session) -> int:
    rows = session.execute(
        select(Sale.accrued_revenue_gr, Sale.paid_amount_gr).where(
            Sale.deleted_at.is_(None),
            Sale.is_cancelled.is_(False),
            Sale.payment_status.in_([PaymentStatus.UNPAID.value, PaymentStatus.PARTIAL.value]),
        )
    ).all()
    return sum(max(accrued - paid, 0) for accrued, paid in rows)


# --- ewidencja sprzedaży ---


@dataclass
class RegistryResult:
    rows: list[dict]
    total_accrued_gr: int
    total_count: int
    page: int
    per_page: int


def sales_registry(
    session: Session, filters: SaleFilters, *, page: int = 1, per_page: int = 50
) -> RegistryResult:
    """Ewidencja z przychodem narastająco liczonym od początku wybranego okresu."""
    stmt = base_query(filters).order_by(Sale.sale_date.asc(), Sale.id.asc()).limit(MAX_REGISTRY_ROWS)
    sales = list(session.execute(stmt).scalars())

    rows: list[dict] = []
    cumulative = 0
    for index, sale in enumerate(sales, start=1):
        cumulative += sale.accrued_revenue_gr
        rows.append(
            {
                "lp": index,
                "sale_id": sale.id,
                "sale_date": sale.sale_date,
                "document_number": sale.document_number,
                "description": sale.description,
                "total_gr": sale.total_gr,
                "corrections_total_gr": sale.corrections_total_gr,
                "accrued_revenue_gr": sale.accrued_revenue_gr,
                "cumulative_gr": cumulative,
                "payment_status": sale.payment_status,
                "paid_amount_gr": sale.paid_amount_gr,
            }
        )

    total_count = len(rows)
    start = max(page - 1, 0) * per_page
    page_rows = rows[start : start + per_page]
    return RegistryResult(
        rows=page_rows, total_accrued_gr=cumulative, total_count=total_count, page=page, per_page=per_page
    )


def daily_registry(session: Session, filters: SaleFilters) -> list[dict]:
    """Uproszczona ewidencja dzienna z wartością narastająco."""
    stmt = base_query(filters).order_by(Sale.sale_date.asc(), Sale.id.asc()).limit(MAX_REGISTRY_ROWS)
    sales = list(session.execute(stmt).scalars())

    per_day: dict[date, dict[str, int]] = defaultdict(lambda: {"count": 0, "total_gr": 0})
    for sale in sales:
        bucket = per_day[sale.sale_date]
        bucket["count"] += 1
        bucket["total_gr"] += sale.accrued_revenue_gr

    rows: list[dict] = []
    cumulative = 0
    for index, (day, bucket) in enumerate(sorted(per_day.items()), start=1):
        cumulative += bucket["total_gr"]
        rows.append(
            {
                "lp": index,
                "day": day,
                "sales_count": bucket["count"],
                "total_gr": bucket["total_gr"],
                "cumulative_gr": cumulative,
            }
        )
    return rows


# --- serie do wykresów ---


def daily_series(session: Session, date_from: date, date_to: date) -> list[dict]:
    sales = session.execute(
        select(Sale.sale_date, Sale.accrued_revenue_gr).where(
            Sale.deleted_at.is_(None), Sale.sale_date >= date_from, Sale.sale_date <= date_to
        )
    ).all()
    payments = session.execute(
        select(Payment.payment_date, Payment.amount_gr)
        .join(Sale, Sale.id == Payment.sale_id)
        .where(
            Payment.deleted_at.is_(None),
            Sale.deleted_at.is_(None),
            Payment.payment_date >= date_from,
            Payment.payment_date <= date_to,
        )
    ).all()

    accrued: dict[date, int] = defaultdict(int)
    received: dict[date, int] = defaultdict(int)
    for day, amount in sales:
        accrued[day] += amount
    for day, amount in payments:
        received[day] += amount

    series: list[dict] = []
    current = date_from
    while current <= date_to:
        series.append(
            {
                "day": current,
                "accrued_gr": accrued.get(current, 0),
                "received_gr": received.get(current, 0),
            }
        )
        current += timedelta(days=1)
    return series


def monthly_series(session: Session, year: int) -> list[dict]:
    result: list[dict] = []
    for month in range(1, 13):
        date_from, date_to = month_range(year, month)
        accrued = accrued_sum(session, date_from, date_to)
        received = received_sum(session, date_from, date_to)
        costs = costs_sum(session, date_from, date_to)
        result.append(
            {
                "year": year,
                "month": month,
                "label": MONTH_NAMES_PL[month],
                "accrued_gr": accrued,
                "received_gr": received,
                "costs_gr": costs,
                "income_gr": received - costs,
                "sales_count": sales_count(session, date_from, date_to),
            }
        )
    return result


def quarterly_series(session: Session, year: int) -> list[dict]:
    result: list[dict] = []
    for quarter in (1, 2, 3, 4):
        date_from, date_to = quarter_range(year, quarter)
        accrued = accrued_sum(session, date_from, date_to)
        received = received_sum(session, date_from, date_to)
        costs = costs_sum(session, date_from, date_to)
        result.append(
            {
                "year": year,
                "quarter": quarter,
                "label": f"Q{quarter}",
                "accrued_gr": accrued,
                "received_gr": received,
                "costs_gr": costs,
                "income_gr": received - costs,
                "sales_count": sales_count(session, date_from, date_to),
            }
        )
    return result


def by_channel(session: Session, date_from: date, date_to: date) -> list[dict]:
    rows = session.execute(
        select(
            Sale.sales_channel,
            func.coalesce(func.sum(Sale.accrued_revenue_gr), 0),
            func.count(Sale.id),
        )
        .where(Sale.deleted_at.is_(None), Sale.sale_date >= date_from, Sale.sale_date <= date_to)
        .group_by(Sale.sales_channel)
    ).all()
    return [
        {"channel": channel or "inne", "accrued_gr": int(total), "sales_count": int(count)}
        for channel, total, count in sorted(rows, key=lambda row: -int(row[1]))
    ]


def by_product(session: Session, date_from: date, date_to: date, limit: int = 20) -> list[dict]:
    rows = session.execute(
        select(
            SaleItem.product_id,
            SaleItem.name,
            func.coalesce(func.sum(SaleItem.line_total_gr), 0),
            func.coalesce(func.sum(SaleItem.quantity), 0),
        )
        .join(Sale, Sale.id == SaleItem.sale_id)
        .where(
            Sale.deleted_at.is_(None),
            Sale.is_cancelled.is_(False),
            Sale.sale_date >= date_from,
            Sale.sale_date <= date_to,
        )
        .group_by(SaleItem.product_id, SaleItem.name)
        .order_by(func.coalesce(func.sum(SaleItem.line_total_gr), 0).desc())
        .limit(limit)
    ).all()
    return [
        {
            "product_id": product_id,
            "name": name,
            "value_gr": int(value),
            "quantity": int(quantity),
        }
        for product_id, name, value, quantity in rows
    ]


def by_customer_type(session: Session, date_from: date, date_to: date) -> list[dict]:
    result = []
    for customer_type in (CustomerType.B2C.value, CustomerType.B2B.value):
        value = accrued_sum(session, date_from, date_to, customer_type=customer_type)
        count = int(
            session.execute(
                select(func.count(Sale.id)).where(
                    Sale.deleted_at.is_(None),
                    Sale.sale_date >= date_from,
                    Sale.sale_date <= date_to,
                    Sale.customer_type == customer_type,
                )
            ).scalar_one()
        )
        result.append({"customer_type": customer_type, "accrued_gr": value, "sales_count": count})
    return result


def costs_by_category(session: Session, date_from: date, date_to: date) -> list[dict]:
    rows = session.execute(
        select(
            CostCategory.name,
            func.coalesce(func.sum(Cost.amount_gr), 0),
            func.count(Cost.id),
        )
        .select_from(Cost)
        .outerjoin(CostCategory, CostCategory.id == Cost.category_id)
        .where(Cost.deleted_at.is_(None), Cost.cost_date >= date_from, Cost.cost_date <= date_to)
        .group_by(CostCategory.name)
        .order_by(func.coalesce(func.sum(Cost.amount_gr), 0).desc())
    ).all()
    return [
        {"category": name or "bez kategorii", "amount_gr": int(total), "count": int(count)}
        for name, total, count in rows
    ]


def unpaid_receivables(session: Session) -> list[dict]:
    sales = session.execute(
        select(Sale)
        .where(
            Sale.deleted_at.is_(None),
            Sale.is_cancelled.is_(False),
            Sale.payment_status.in_([PaymentStatus.UNPAID.value, PaymentStatus.PARTIAL.value]),
        )
        .order_by(Sale.sale_date.asc())
    ).scalars()
    today = today_local()
    rows = []
    for sale in sales:
        outstanding = max(sale.accrued_revenue_gr - sale.paid_amount_gr, 0)
        if outstanding <= 0:
            continue
        rows.append(
            {
                "sale_id": sale.id,
                "document_number": sale.document_number,
                "sale_date": sale.sale_date,
                "customer_name": sale.customer_name,
                "accrued_revenue_gr": sale.accrued_revenue_gr,
                "paid_amount_gr": sale.paid_amount_gr,
                "outstanding_gr": outstanding,
                "days_overdue": (today - sale.sale_date).days,
                "payment_status": sale.payment_status,
            }
        )
    return rows


# --- definicje raportów do eksportu ---


@dataclass
class ReportDefinition:
    key: str
    title: str
    columns: list[tuple[str, str, str]]  # (klucz, nagłówek, typ: text|money|date|int)
    rows: list[dict] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)


def _period_bounds(year: int, quarter: int | None, month: int | None) -> tuple[date, date]:
    if quarter:
        return quarter_range(year, quarter)
    if month:
        return month_range(year, month)
    return year_range(year)


def build_report(
    session: Session,
    key: str,
    *,
    year: int | None = None,
    quarter: int | None = None,
    month: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> ReportDefinition:
    today = today_local()
    year = year or today.year
    if date_from is None or date_to is None:
        date_from, date_to = _period_bounds(year, quarter, month)

    if key == "sprzedaz_dzienna":
        rows = daily_registry(session, SaleFilters(date_from=date_from, date_to=date_to))
        return ReportDefinition(
            key=key,
            title="Sprzedaż dzienna",
            columns=[
                ("lp", "Lp.", "int"),
                ("day", "Data", "date"),
                ("sales_count", "Liczba sprzedaży", "int"),
                ("total_gr", "Wartość sprzedaży", "money"),
                ("cumulative_gr", "Narastająco", "money"),
            ],
            rows=rows,
            summary={"total_gr": sum(row["total_gr"] for row in rows)},
        )

    if key == "sprzedaz_miesieczna":
        rows = monthly_series(session, year)
        return ReportDefinition(
            key=key,
            title=f"Sprzedaż miesięczna {year}",
            columns=[
                ("label", "Miesiąc", "text"),
                ("sales_count", "Liczba sprzedaży", "int"),
                ("accrued_gr", "Przychód należny", "money"),
                ("received_gr", "Przychód otrzymany", "money"),
                ("costs_gr", "Koszty", "money"),
                ("income_gr", "Dochód", "money"),
            ],
            rows=rows,
            summary={
                "accrued_gr": sum(row["accrued_gr"] for row in rows),
                "received_gr": sum(row["received_gr"] for row in rows),
                "costs_gr": sum(row["costs_gr"] for row in rows),
                "income_gr": sum(row["income_gr"] for row in rows),
            },
        )

    if key == "sprzedaz_kwartalna":
        rows = quarterly_series(session, year)
        return ReportDefinition(
            key=key,
            title=f"Sprzedaż kwartalna {year}",
            columns=[
                ("label", "Kwartał", "text"),
                ("sales_count", "Liczba sprzedaży", "int"),
                ("accrued_gr", "Przychód należny", "money"),
                ("received_gr", "Przychód otrzymany", "money"),
                ("costs_gr", "Koszty", "money"),
                ("income_gr", "Dochód", "money"),
            ],
            rows=rows,
            summary={
                "accrued_gr": sum(row["accrued_gr"] for row in rows),
                "received_gr": sum(row["received_gr"] for row in rows),
                "costs_gr": sum(row["costs_gr"] for row in rows),
            },
        )

    if key == "sprzedaz_roczna":
        rows = [
            {
                "label": str(year),
                "accrued_gr": accrued_sum(session, *year_range(year)),
                "received_gr": received_sum(session, *year_range(year)),
                "costs_gr": costs_sum(session, *year_range(year)),
                "sales_count": sales_count(session, *year_range(year)),
            }
        ]
        rows[0]["income_gr"] = rows[0]["received_gr"] - rows[0]["costs_gr"]
        return ReportDefinition(
            key=key,
            title=f"Sprzedaż roczna {year}",
            columns=[
                ("label", "Rok", "text"),
                ("sales_count", "Liczba sprzedaży", "int"),
                ("accrued_gr", "Przychód należny", "money"),
                ("received_gr", "Przychód otrzymany", "money"),
                ("costs_gr", "Koszty", "money"),
                ("income_gr", "Dochód", "money"),
            ],
            rows=rows,
        )

    if key == "ewidencja_sprzedazy":
        result = sales_registry(
            session, SaleFilters(date_from=date_from, date_to=date_to), page=1, per_page=MAX_REGISTRY_ROWS
        )
        return ReportDefinition(
            key=key,
            title="Ewidencja sprzedaży",
            columns=[
                ("lp", "Lp.", "int"),
                ("sale_date", "Data", "date"),
                ("document_number", "Numer sprzedaży", "text"),
                ("description", "Opis", "text"),
                ("total_gr", "Kwota sprzedaży", "money"),
                ("corrections_total_gr", "Korekty", "money"),
                ("accrued_revenue_gr", "Przychód należny", "money"),
                ("cumulative_gr", "Narastająco", "money"),
                ("payment_status", "Status płatności", "text"),
                ("paid_amount_gr", "Kwota otrzymana", "money"),
            ],
            rows=result.rows,
            summary={"accrued_revenue_gr": result.total_accrued_gr},
        )

    if key == "przychod_nalezny":
        rows = quarterly_series(session, year)
        return ReportDefinition(
            key=key,
            title=f"Przychód należny {year}",
            columns=[
                ("label", "Kwartał", "text"),
                ("accrued_gr", "Przychód należny", "money"),
            ],
            rows=rows,
            summary={"accrued_gr": sum(row["accrued_gr"] for row in rows)},
        )

    if key == "przychod_otrzymany":
        rows = monthly_series(session, year)
        return ReportDefinition(
            key=key,
            title=f"Przychód otrzymany {year}",
            columns=[("label", "Miesiąc", "text"), ("received_gr", "Przychód otrzymany", "money")],
            rows=rows,
            summary={"received_gr": sum(row["received_gr"] for row in rows)},
        )

    if key == "koszty":
        rows = costs_by_category(session, date_from, date_to)
        return ReportDefinition(
            key=key,
            title="Koszty według kategorii",
            columns=[
                ("category", "Kategoria", "text"),
                ("count", "Liczba", "int"),
                ("amount_gr", "Kwota", "money"),
            ],
            rows=rows,
            summary={"amount_gr": sum(row["amount_gr"] for row in rows)},
        )

    if key == "dochod":
        rows = monthly_series(session, year)
        return ReportDefinition(
            key=key,
            title=f"Dochód {year}",
            columns=[
                ("label", "Miesiąc", "text"),
                ("received_gr", "Przychód otrzymany", "money"),
                ("costs_gr", "Koszty", "money"),
                ("income_gr", "Dochód", "money"),
            ],
            rows=rows,
            summary={"income_gr": sum(row["income_gr"] for row in rows)},
        )

    if key in ("sprzedaz_b2c", "sprzedaz_b2b"):
        customer_type = CustomerType.B2C.value if key.endswith("b2c") else CustomerType.B2B.value
        sales = session.execute(
            select(Sale)
            .where(
                Sale.deleted_at.is_(None),
                Sale.customer_type == customer_type,
                Sale.sale_date >= date_from,
                Sale.sale_date <= date_to,
            )
            .order_by(Sale.sale_date.asc())
        ).scalars()
        rows = [
            {
                "sale_date": sale.sale_date,
                "document_number": sale.document_number,
                "customer_name": sale.customer_name,
                "accrued_revenue_gr": sale.accrued_revenue_gr,
                "paid_amount_gr": sale.paid_amount_gr,
            }
            for sale in sales
        ]
        return ReportDefinition(
            key=key,
            title="Sprzedaż " + ("B2C" if customer_type == CustomerType.B2C.value else "B2B"),
            columns=[
                ("sale_date", "Data", "date"),
                ("document_number", "Numer", "text"),
                ("customer_name", "Klient", "text"),
                ("accrued_revenue_gr", "Przychód należny", "money"),
                ("paid_amount_gr", "Otrzymano", "money"),
            ],
            rows=rows,
            summary={"accrued_revenue_gr": sum(row["accrued_revenue_gr"] for row in rows)},
        )

    if key == "sprzedaz_wg_produktu":
        rows = by_product(session, date_from, date_to, limit=500)
        return ReportDefinition(
            key=key,
            title="Sprzedaż według produktu",
            columns=[
                ("name", "Produkt", "text"),
                ("quantity", "Ilość", "int"),
                ("value_gr", "Wartość", "money"),
            ],
            rows=rows,
            summary={"value_gr": sum(row["value_gr"] for row in rows)},
        )

    if key == "sprzedaz_wg_kanalu":
        rows = by_channel(session, date_from, date_to)
        return ReportDefinition(
            key=key,
            title="Sprzedaż według kanału",
            columns=[
                ("channel", "Kanał", "text"),
                ("sales_count", "Liczba sprzedaży", "int"),
                ("accrued_gr", "Przychód należny", "money"),
            ],
            rows=rows,
            summary={"accrued_gr": sum(row["accrued_gr"] for row in rows)},
        )

    if key == "naleznosci_niezaplacone":
        rows = unpaid_receivables(session)
        return ReportDefinition(
            key=key,
            title="Niezapłacone należności",
            columns=[
                ("sale_date", "Data", "date"),
                ("document_number", "Numer", "text"),
                ("customer_name", "Klient", "text"),
                ("accrued_revenue_gr", "Przychód należny", "money"),
                ("paid_amount_gr", "Otrzymano", "money"),
                ("outstanding_gr", "Pozostało", "money"),
                ("days_overdue", "Dni od sprzedaży", "int"),
            ],
            rows=rows,
            summary={"outstanding_gr": sum(row["outstanding_gr"] for row in rows)},
        )

    raise ValueError(f"Nieznany raport: {key}")


AVAILABLE_REPORTS = [
    ("sprzedaz_dzienna", "Sprzedaż dzienna"),
    ("sprzedaz_miesieczna", "Sprzedaż miesięczna"),
    ("sprzedaz_kwartalna", "Sprzedaż kwartalna"),
    ("sprzedaz_roczna", "Sprzedaż roczna"),
    ("ewidencja_sprzedazy", "Ewidencja sprzedaży"),
    ("przychod_nalezny", "Przychód należny"),
    ("przychod_otrzymany", "Przychód otrzymany"),
    ("koszty", "Koszty"),
    ("dochod", "Dochód"),
    ("sprzedaz_b2c", "Sprzedaż B2C"),
    ("sprzedaz_b2b", "Sprzedaż B2B"),
    ("sprzedaz_wg_produktu", "Sprzedaż według produktu"),
    ("sprzedaz_wg_kanalu", "Sprzedaż według kanału"),
    ("naleznosci_niezaplacone", "Niezapłacone należności"),
]


def current_quarter(today: date | None = None) -> tuple[int, int]:
    today = today or today_local()
    return today.year, quarter_of(today)
