"""Zależności FastAPI: sesja bazy, bieżący użytkownik, ochrona CSRF i role."""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AuthError, PermissionError_
from app.core.security import constant_time_compare
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User, UserSession
from app.services import auth_service

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def db_session() -> Generator[Session, None, None]:
    yield from get_db()


def client_ip(request: Request) -> str | None:
    """Adres klienta — za reverse proxy bierzemy pierwszy wpis X-Forwarded-For."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    if request.client:
        return request.client.host
    return None


@dataclass
class CurrentUser:
    user: User
    session: UserSession
    ip: str | None


def get_current_context(
    request: Request, session: Session = Depends(db_session)
) -> CurrentUser:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    resolved = auth_service.resolve_session(session, token)
    if resolved is None:
        raise AuthError("Sesja wygasła lub nie jesteś zalogowany.")
    user, user_session = resolved
    session.commit()

    if request.method not in SAFE_METHODS:
        header_token = request.headers.get(settings.csrf_header_name, "")
        cookie_token = request.cookies.get(settings.csrf_cookie_name, "")
        if not header_token or not constant_time_compare(header_token, user_session.csrf_token):
            raise PermissionError_("Nieprawidłowy token CSRF. Odśwież stronę i spróbuj ponownie.")
        if cookie_token and not constant_time_compare(cookie_token, user_session.csrf_token):
            raise PermissionError_("Nieprawidłowy token CSRF. Odśwież stronę i spróbuj ponownie.")
    return CurrentUser(user=user, session=user_session, ip=client_ip(request))


def current_user(context: CurrentUser = Depends(get_current_context)) -> User:
    return context.user


def require_admin(context: CurrentUser = Depends(get_current_context)) -> CurrentUser:
    if context.user.role != UserRole.ADMIN.value:
        raise PermissionError_("Ta operacja wymaga uprawnień administratora.")
    return context


def require_write(context: CurrentUser = Depends(get_current_context)) -> CurrentUser:
    """Rola 'podgląd' może tylko czytać."""
    if context.user.role == UserRole.VIEWER.value:
        raise PermissionError_("Twoja rola pozwala wyłącznie na przeglądanie danych.")
    return context
