"""Logowanie, wylogowanie, sesja i zmiana hasła."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, client_ip, db_session, get_current_context
from app.core.config import get_settings
from app.models.enums import AuditAction
from app.schemas.auth import LoginRequest, PasswordChangeRequest, SessionInfo, UserOut
from app.schemas.common import MessageResponse
from app.services import audit_service, auth_service

router = APIRouter(prefix="/auth", tags=["autoryzacja"])


def _set_cookies(response: Response, token: str, csrf_token: str) -> None:
    settings = get_settings()
    max_age = settings.session_idle_minutes * 60
    common = {
        "secure": settings.cookies_secure,
        "samesite": settings.cookie_samesite,
        "path": "/",
        "max_age": max_age,
    }
    if settings.cookie_domain:
        common["domain"] = settings.cookie_domain
    response.set_cookie(settings.session_cookie_name, token, httponly=True, **common)
    # Token CSRF musi być czytelny dla frontendu (wzorzec double submit).
    response.set_cookie(settings.csrf_cookie_name, csrf_token, httponly=False, **common)


def _clear_cookies(response: Response) -> None:
    settings = get_settings()
    kwargs = {"path": "/"}
    if settings.cookie_domain:
        kwargs["domain"] = settings.cookie_domain
    response.delete_cookie(settings.session_cookie_name, **kwargs)
    response.delete_cookie(settings.csrf_cookie_name, **kwargs)


@router.post("/login", response_model=SessionInfo)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: Session = Depends(db_session),
) -> SessionInfo:
    ip = client_ip(request)
    try:
        result = auth_service.authenticate(
            session,
            payload.login,
            payload.password,
            ip=ip,
            user_agent=request.headers.get("user-agent"),
        )
    except Exception:
        session.commit()  # zapisujemy próbę logowania i wpis audytu
        raise
    session.commit()
    _set_cookies(response, result.token, result.csrf_token)
    return SessionInfo(
        user=UserOut.model_validate(result.user),
        csrf_token=result.csrf_token,
        expires_at=result.expires_at,
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response,
    context: CurrentUser = Depends(get_current_context),
    session: Session = Depends(db_session),
) -> MessageResponse:
    auth_service.revoke_session(session, context.session)
    audit_service.record(
        session, AuditAction.LOGOUT, user=context.user, ip_address=context.ip, description="Wylogowano."
    )
    session.commit()
    _clear_cookies(response)
    return MessageResponse(message="Wylogowano.")


@router.get("/me", response_model=SessionInfo)
def me(context: CurrentUser = Depends(get_current_context)) -> SessionInfo:
    return SessionInfo(
        user=UserOut.model_validate(context.user),
        csrf_token=context.session.csrf_token,
        expires_at=context.session.expires_at,
    )


@router.post("/password", response_model=MessageResponse)
def change_password(
    payload: PasswordChangeRequest,
    context: CurrentUser = Depends(get_current_context),
    session: Session = Depends(db_session),
) -> MessageResponse:
    auth_service.change_password(
        session, context.user, payload.current_password, payload.new_password, ip=context.ip
    )
    auth_service.revoke_all_sessions(session, context.user.id, keep_session_id=context.session.id)
    session.commit()
    return MessageResponse(message="Hasło zostało zmienione.")
