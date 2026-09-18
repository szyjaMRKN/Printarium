"""Ustawienia aplikacji i parametry lat podatkowych."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, db_session, get_current_context, require_admin
from app.models.enums import AuditAction
from app.schemas.settings import FiscalYearOut, FiscalYearUpdate, SettingsOut, SettingsUpdate
from app.services import audit_service
from app.services.settings_service import DEFAULT_SETTINGS, SettingsService

router = APIRouter(prefix="/settings", tags=["ustawienia"])


def _params_to_out(params) -> FiscalYearOut:
    return FiscalYearOut(
        year=params.year,
        minimum_wage_gr=params.minimum_wage_gr,
        limit_multiplier_permille=params.limit_multiplier_permille,
        quarterly_limit_gr=params.quarterly_limit_gr,
        quarterly_limit_override_gr=params.quarterly_limit_override_gr,
        ksef_monthly_threshold_gr=params.ksef_monthly_threshold_gr,
        cash_register_yearly_threshold_gr=params.cash_register_yearly_threshold_gr,
        note=params.note,
    )


@router.get("", response_model=SettingsOut)
def get_settings_values(
    _: CurrentUser = Depends(get_current_context), session: Session = Depends(db_session)
) -> SettingsOut:
    return SettingsOut(values=SettingsService(session).all())


@router.get("/schema")
def settings_schema(_: CurrentUser = Depends(get_current_context)) -> list[dict]:
    """Lista dostępnych kluczy ustawień wraz z typem — używana przez interfejs."""
    return [
        {"key": key, "type": value_type, "default": default}
        for key, (value_type, default) in DEFAULT_SETTINGS.items()
    ]


@router.put("", response_model=SettingsOut)
def update_settings(
    payload: SettingsUpdate,
    context: CurrentUser = Depends(require_admin),
    session: Session = Depends(db_session),
) -> SettingsOut:
    service = SettingsService(session)
    values = service.set_many(payload.values)
    audit_service.record(
        session,
        AuditAction.SETTINGS_UPDATE,
        user=context.user,
        entity_type="settings",
        ip_address=context.ip,
        description="Zmieniono ustawienia: " + ", ".join(sorted(payload.values)),
    )
    session.commit()
    return SettingsOut(values=values)


@router.get("/fiscal-years", response_model=list[FiscalYearOut])
def list_fiscal_years(
    _: CurrentUser = Depends(get_current_context), session: Session = Depends(db_session)
) -> list[FiscalYearOut]:
    service = SettingsService(session)
    years = [_params_to_out(params) for params in service.list_fiscal_years()]
    session.commit()
    return years


@router.get("/fiscal-years/{year}", response_model=FiscalYearOut)
def get_fiscal_year(
    year: int,
    _: CurrentUser = Depends(get_current_context),
    session: Session = Depends(db_session),
) -> FiscalYearOut:
    service = SettingsService(session)
    params = service.fiscal_params(year)
    session.commit()
    return _params_to_out(params)


@router.put("/fiscal-years/{year}", response_model=FiscalYearOut)
def update_fiscal_year(
    year: int,
    payload: FiscalYearUpdate,
    context: CurrentUser = Depends(require_admin),
    session: Session = Depends(db_session),
) -> FiscalYearOut:
    service = SettingsService(session)
    params = service.update_fiscal_year(year, payload.model_dump(exclude_unset=True))
    audit_service.record(
        session,
        AuditAction.SETTINGS_UPDATE,
        user=context.user,
        entity_type="fiscal_year",
        entity_id=year,
        ip_address=context.ip,
        description=f"Zmieniono parametry roku {year} (limit kwartalny: {params.quarterly_limit_gr} gr).",
    )
    session.commit()
    return _params_to_out(params)
