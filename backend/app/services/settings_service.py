"""Ustawienia aplikacji i parametry roku podatkowego.

Wszystkie wartości, które mogą się zmienić (limity, progi, mnożniki, dane
sprzedawcy, numeracja dokumentów), trzymamy w bazie. Kod liczący pobiera je
stąd, nigdy nie zawiera ich na sztywno.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dates import today_local
from app.core.money import apply_multiplier
from app.models.setting import FiscalYear, Setting

BOOL = "bool"
INT = "int"
STR = "string"
JSON_TYPE = "json"

# Wartości startowe. Po pierwszym uruchomieniu użytkownik zmienia je w UI,
# a nie w kodzie.
DEFAULT_SETTINGS: dict[str, tuple[str, Any]] = {
    # --- rok podatkowy / działalność nierejestrowana ---
    "fiscal.default_year": (INT, 0),  # 0 => bieżący rok kalendarzowy
    "fiscal.shipping_counts_as_revenue": (BOOL, True),
    "fiscal.warning_percent": (INT, 75),
    "fiscal.strong_warning_percent": (INT, 90),
    # --- dane sprzedawcy (dokumenty) ---
    "company.first_name": (STR, ""),
    "company.last_name": (STR, ""),
    "company.business_name": (STR, ""),
    "company.address": (STR, ""),
    "company.postal_code": (STR, ""),
    "company.city": (STR, ""),
    "company.nip": (STR, ""),
    "company.email": (STR, ""),
    "company.phone": (STR, ""),
    "company.bank_account": (STR, ""),
    # --- numeracja dokumentów ---
    "invoicing.number_format": (STR, "{nr}/{mm}/{rrrr}"),
    "invoicing.reset_period": (STR, "month"),  # month | year
    "invoicing.default_document_type": (STR, "rachunek"),
    "invoicing.default_payment_days": (INT, 7),
    "invoicing.footer_note": (
        STR,
        "Sprzedawca korzysta ze zwolnienia podmiotowego z VAT (art. 113 ust. 1 ustawy o VAT).",
    ),
    # --- pliki ---
    "uploads.max_size_mb": (INT, 10),
    "uploads.allowed_extensions": (JSON_TYPE, ["pdf", "jpg", "jpeg", "png", "webp"]),
    # --- backup ---
    "backup.auto_enabled": (BOOL, True),
    "backup.auto_hour": (INT, 3),
    "backup.auto_minute": (INT, 0),
    "backup.retention": (INT, 30),
}

# Parametry startowe roku podatkowego (limit 225% minimalnego wynagrodzenia).
DEFAULT_FISCAL_YEAR: dict[str, int] = {
    "minimum_wage_gr": 480_600,
    "limit_multiplier_permille": 2250,
    "ksef_monthly_threshold_gr": 1_000_000,
    "cash_register_yearly_threshold_gr": 2_000_000,
}


@dataclass(frozen=True)
class FiscalYearParams:
    """Parametry roku wraz z wyliczonym limitem kwartalnym."""

    year: int
    minimum_wage_gr: int
    limit_multiplier_permille: int
    quarterly_limit_gr: int
    quarterly_limit_override_gr: int | None
    ksef_monthly_threshold_gr: int
    cash_register_yearly_threshold_gr: int
    note: str | None = None


def _encode(value: Any, value_type: str) -> str:
    if value_type == BOOL:
        return "1" if value else "0"
    if value_type == INT:
        return str(int(value))
    if value_type == JSON_TYPE:
        return json.dumps(value, ensure_ascii=False)
    return "" if value is None else str(value)


def _decode(raw: str | None, value_type: str) -> Any:
    if raw is None:
        return None
    if value_type == BOOL:
        return raw in ("1", "true", "True")
    if value_type == INT:
        try:
            return int(raw)
        except ValueError:
            return 0
    if value_type == JSON_TYPE:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
    return raw


class SettingsService:
    def __init__(self, session: Session) -> None:
        self.session = session

    # --- ustawienia klucz/wartość ---

    def all(self) -> dict[str, Any]:
        stored = {row.key: row for row in self.session.execute(select(Setting)).scalars()}
        result: dict[str, Any] = {}
        for key, (value_type, default) in DEFAULT_SETTINGS.items():
            row = stored.get(key)
            if row is None:
                result[key] = default
            else:
                decoded = _decode(row.value, value_type)
                result[key] = default if decoded is None else decoded
        return result

    def get(self, key: str) -> Any:
        if key not in DEFAULT_SETTINGS:
            raise KeyError(f"Nieznane ustawienie: {key}")
        value_type, default = DEFAULT_SETTINGS[key]
        row = self.session.get(Setting, key)
        if row is None or row.value is None:
            return default
        decoded = _decode(row.value, value_type)
        return default if decoded is None else decoded

    def get_int(self, key: str) -> int:
        return int(self.get(key))

    def get_bool(self, key: str) -> bool:
        return bool(self.get(key))

    def get_str(self, key: str) -> str:
        return str(self.get(key) or "")

    def set_many(self, values: dict[str, Any]) -> dict[str, Any]:
        for key, value in values.items():
            if key not in DEFAULT_SETTINGS:
                raise KeyError(f"Nieznane ustawienie: {key}")
            value_type, _ = DEFAULT_SETTINGS[key]
            row = self.session.get(Setting, key)
            encoded = _encode(value, value_type)
            if row is None:
                self.session.add(Setting(key=key, value=encoded, value_type=value_type))
            else:
                row.value = encoded
                row.value_type = value_type
        self.session.flush()
        return self.all()

    # --- rok podatkowy ---

    def default_year(self) -> int:
        configured = self.get_int("fiscal.default_year")
        return configured if configured > 0 else today_local().year

    def get_fiscal_year_row(self, year: int, create: bool = True) -> FiscalYear | None:
        row = self.session.get(FiscalYear, year)
        if row is None and create:
            row = FiscalYear(year=year, **DEFAULT_FISCAL_YEAR)
            self.session.add(row)
            self.session.flush()
        return row

    def fiscal_params(self, year: int) -> FiscalYearParams:
        row = self.get_fiscal_year_row(year)
        assert row is not None
        computed = apply_multiplier(row.minimum_wage_gr, row.limit_multiplier_permille)
        limit = row.quarterly_limit_override_gr if row.quarterly_limit_override_gr else computed
        return FiscalYearParams(
            year=row.year,
            minimum_wage_gr=row.minimum_wage_gr,
            limit_multiplier_permille=row.limit_multiplier_permille,
            quarterly_limit_gr=limit,
            quarterly_limit_override_gr=row.quarterly_limit_override_gr,
            ksef_monthly_threshold_gr=row.ksef_monthly_threshold_gr,
            cash_register_yearly_threshold_gr=row.cash_register_yearly_threshold_gr,
            note=row.note,
        )

    def list_fiscal_years(self) -> list[FiscalYearParams]:
        years = self.session.execute(select(FiscalYear).order_by(FiscalYear.year.desc())).scalars().all()
        if not years:
            self.get_fiscal_year_row(self.default_year())
            years = self.session.execute(select(FiscalYear).order_by(FiscalYear.year.desc())).scalars().all()
        return [self.fiscal_params(row.year) for row in years]

    def update_fiscal_year(self, year: int, values: dict[str, Any]) -> FiscalYearParams:
        row = self.get_fiscal_year_row(year)
        assert row is not None
        for field in (
            "minimum_wage_gr",
            "limit_multiplier_permille",
            "quarterly_limit_override_gr",
            "ksef_monthly_threshold_gr",
            "cash_register_yearly_threshold_gr",
            "note",
        ):
            if field in values:
                setattr(row, field, values[field])
        self.session.flush()
        return self.fiscal_params(year)

    # --- dane sprzedawcy w formie gotowej dla dokumentów ---

    def seller_data(self) -> dict[str, str]:
        values = self.all()
        full_name = " ".join(
            part for part in (values["company.first_name"], values["company.last_name"]) if part
        ).strip()
        return {
            "name": values["company.business_name"] or full_name,
            "person": full_name,
            "address": values["company.address"],
            "postal_code": values["company.postal_code"],
            "city": values["company.city"],
            "nip": values["company.nip"],
            "email": values["company.email"],
            "phone": values["company.phone"],
            "bank_account": values["company.bank_account"],
            "footer_note": values["invoicing.footer_note"],
        }
