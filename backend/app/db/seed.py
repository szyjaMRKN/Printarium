"""Dane początkowe: kategorie kosztów, rok podatkowy, konto administratora."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dates import today_local
from app.models.enums import UserRole
from app.models.user import User
from app.services import auth_service, costs_service
from app.services.settings_service import SettingsService


def seed_reference_data(session: Session) -> None:
    costs_service.ensure_default_categories(session)
    settings_service = SettingsService(session)
    settings_service.get_fiscal_year_row(today_local().year)
    session.flush()


def ensure_admin_from_env(session: Session) -> User | None:
    """Tworzy administratora z ADMIN_LOGIN/ADMIN_PASSWORD, jeśli nie ma użytkowników."""
    settings = get_settings()
    if not settings.admin_login or not settings.admin_password:
        return None
    user_count = int(session.execute(select(func.count(User.id))).scalar_one())
    if user_count > 0:
        return None
    return auth_service.create_user(
        session,
        login=settings.admin_login,
        password=settings.admin_password,
        email=settings.admin_email or None,
        role=UserRole.ADMIN.value,
    )
