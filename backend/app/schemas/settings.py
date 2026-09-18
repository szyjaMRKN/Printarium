from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SettingsOut(BaseModel):
    values: dict[str, Any]


class SettingsUpdate(BaseModel):
    values: dict[str, Any] = Field(default_factory=dict)


class FiscalYearOut(BaseModel):
    year: int
    minimum_wage_gr: int
    limit_multiplier_permille: int
    quarterly_limit_gr: int
    quarterly_limit_override_gr: int | None
    ksef_monthly_threshold_gr: int
    cash_register_yearly_threshold_gr: int
    note: str | None = None


class FiscalYearUpdate(BaseModel):
    minimum_wage_gr: int | None = Field(default=None, ge=0, le=1_000_000_000)
    limit_multiplier_permille: int | None = Field(default=None, ge=0, le=100_000)
    quarterly_limit_override_gr: int | None = Field(default=None, ge=0, le=1_000_000_000)
    ksef_monthly_threshold_gr: int | None = Field(default=None, ge=0, le=1_000_000_000)
    cash_register_yearly_threshold_gr: int | None = Field(default=None, ge=0, le=1_000_000_000)
    note: str | None = Field(default=None, max_length=1000)
