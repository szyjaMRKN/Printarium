"""Logowanie, sesje serwerowe, limit prób i zarządzanie użytkownikami."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dates import utcnow
from app.core.errors import AuthError, ConflictError, NotFoundError, RateLimitError, ValidationError
from app.core.security import (
    generate_token,
    hash_password,
    hash_token,
    needs_rehash,
    password_problems,
    verify_password,
)
from app.models.enums import AuditAction, UserRole
from app.models.user import LoginAttempt, User, UserSession
from app.services import audit_service


class LoginResult:
    def __init__(self, user: User, token: str, csrf_token: str, expires_at: datetime) -> None:
        self.user = user
        self.token = token
        self.csrf_token = csrf_token
        self.expires_at = expires_at


def _record_attempt(session: Session, login: str, ip: str | None, successful: bool) -> None:
    session.add(
        LoginAttempt(login=login[:64], ip_address=ip, successful=successful, created_at=utcnow())
    )
    session.flush()


def recent_failed_attempts(session: Session, login: str, ip: str | None) -> int:
    settings = get_settings()
    window_start = utcnow() - timedelta(minutes=settings.login_window_minutes)
    stmt = select(func.count(LoginAttempt.id)).where(
        LoginAttempt.created_at >= window_start,
        LoginAttempt.successful.is_(False),
    )
    if ip:
        stmt = stmt.where((LoginAttempt.login == login) | (LoginAttempt.ip_address == ip))
    else:
        stmt = stmt.where(LoginAttempt.login == login)
    return int(session.execute(stmt).scalar_one())


def get_user_by_login(session: Session, login: str) -> User | None:
    return session.execute(
        select(User).where(func.lower(User.login) == login.strip().lower(), User.deleted_at.is_(None))
    ).scalar_one_or_none()


def authenticate(
    session: Session,
    login: str,
    password: str,
    *,
    ip: str | None = None,
    user_agent: str | None = None,
) -> LoginResult:
    settings = get_settings()
    login = (login or "").strip()
    if not login or not password:
        raise ValidationError("Podaj login i hasło.")

    if recent_failed_attempts(session, login, ip) >= settings.login_max_attempts:
        audit_service.record(
            session,
            AuditAction.LOGIN_FAILED,
            user_login=login,
            ip_address=ip,
            description="Przekroczono limit prób logowania.",
        )
        raise RateLimitError(
            f"Zbyt wiele nieudanych prób logowania. Spróbuj ponownie za {settings.login_lock_minutes} minut."
        )

    user = get_user_by_login(session, login)
    now = utcnow()

    if user is None or not verify_password(password, user.password_hash):
        _record_attempt(session, login, ip, False)
        if user is not None:
            user.failed_login_count += 1
            if user.failed_login_count >= settings.login_max_attempts:
                user.locked_until = now + timedelta(minutes=settings.login_lock_minutes)
        audit_service.record(
            session,
            AuditAction.LOGIN_FAILED,
            user=user,
            user_login=login,
            ip_address=ip,
            description="Nieprawidłowy login lub hasło.",
        )
        raise AuthError("Nieprawidłowy login lub hasło.")

    if not user.is_active:
        _record_attempt(session, login, ip, False)
        audit_service.record(
            session, AuditAction.LOGIN_FAILED, user=user, ip_address=ip, description="Konto nieaktywne."
        )
        raise AuthError("Konto jest nieaktywne. Skontaktuj się z administratorem.")

    locked_until = user.locked_until
    if locked_until is not None and locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=now.tzinfo)
    if locked_until is not None and locked_until > now:
        _record_attempt(session, login, ip, False)
        raise RateLimitError("Konto jest tymczasowo zablokowane po nieudanych próbach logowania.")

    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)

    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = now
    _record_attempt(session, login, ip, True)

    token, csrf_token, user_session = create_user_session(session, user, ip=ip, user_agent=user_agent)
    audit_service.record(session, AuditAction.LOGIN, user=user, ip_address=ip, description="Zalogowano.")
    return LoginResult(user=user, token=token, csrf_token=csrf_token, expires_at=user_session.expires_at)


def create_user_session(
    session: Session, user: User, *, ip: str | None = None, user_agent: str | None = None
) -> tuple[str, str, UserSession]:
    settings = get_settings()
    now = utcnow()
    token = generate_token()
    csrf_token = generate_token(24)
    user_session = UserSession(
        user_id=user.id,
        token_hash=hash_token(token),
        csrf_token=csrf_token,
        created_at=now,
        last_seen_at=now,
        expires_at=now + timedelta(minutes=settings.session_idle_minutes),
        ip_address=ip,
        user_agent=(user_agent or "")[:255] or None,
    )
    session.add(user_session)
    session.flush()
    return token, csrf_token, user_session


def resolve_session(session: Session, token: str | None) -> tuple[User, UserSession] | None:
    """Zwraca użytkownika dla tokenu z ciasteczka albo None."""
    if not token:
        return None
    settings = get_settings()
    now = utcnow()
    user_session = session.execute(
        select(UserSession).where(UserSession.token_hash == hash_token(token))
    ).scalar_one_or_none()
    if user_session is None or user_session.revoked_at is not None:
        return None

    expires_at = user_session.expires_at
    created_at = user_session.created_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=now.tzinfo)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=now.tzinfo)
    if expires_at <= now or created_at + timedelta(hours=settings.session_absolute_hours) <= now:
        user_session.revoked_at = now
        session.flush()
        return None

    user = session.get(User, user_session.user_id)
    if user is None or not user.is_active or user.deleted_at is not None:
        return None

    # Przedłużenie sesji (sliding expiration) — zapis rzadki, żeby nie bić po bazie.
    last_seen = user_session.last_seen_at
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=now.tzinfo)
    if (now - last_seen).total_seconds() > 60:
        user_session.last_seen_at = now
        user_session.expires_at = now + timedelta(minutes=settings.session_idle_minutes)
        session.flush()
    return user, user_session


def revoke_session(session: Session, user_session: UserSession) -> None:
    user_session.revoked_at = utcnow()
    session.flush()


def revoke_all_sessions(session: Session, user_id: int, *, keep_session_id: int | None = None) -> None:
    sessions = session.execute(
        select(UserSession).where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
    ).scalars()
    now = utcnow()
    for item in sessions:
        if keep_session_id is not None and item.id == keep_session_id:
            continue
        item.revoked_at = now
    session.flush()


def change_password(
    session: Session, user: User, current_password: str, new_password: str, *, ip: str | None = None
) -> None:
    if not verify_password(current_password, user.password_hash):
        raise AuthError("Aktualne hasło jest nieprawidłowe.")
    set_password(session, user, new_password)
    audit_service.record(
        session, AuditAction.PASSWORD_CHANGE, user=user, ip_address=ip, description="Zmieniono własne hasło."
    )


def set_password(session: Session, user: User, new_password: str) -> None:
    problems = password_problems(new_password)
    if problems:
        raise ValidationError(" ".join(problems))
    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    session.flush()


def create_user(
    session: Session,
    *,
    login: str,
    password: str,
    email: str | None = None,
    role: str = UserRole.ADMIN.value,
    is_active: bool = True,
) -> User:
    login = (login or "").strip()
    if len(login) < 3:
        raise ValidationError("Login musi mieć co najmniej 3 znaki.")
    if get_user_by_login(session, login) is not None:
        raise ConflictError("Użytkownik o takim loginie już istnieje.")
    problems = password_problems(password)
    if problems:
        raise ValidationError(" ".join(problems))
    user = User(
        login=login,
        email=(email or None),
        password_hash=hash_password(password),
        role=role,
        is_active=is_active,
    )
    session.add(user)
    session.flush()
    return user


def update_user(
    session: Session,
    user_id: int,
    *,
    email: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    new_password: str | None = None,
) -> User:
    user = session.get(User, user_id)
    if user is None or user.deleted_at is not None:
        raise NotFoundError("Nie znaleziono użytkownika.")
    if email is not None:
        user.email = email or None
    if role is not None:
        user.role = role
    if is_active is not None:
        user.is_active = is_active
        if not is_active:
            revoke_all_sessions(session, user.id)
    if new_password:
        set_password(session, user, new_password)
        revoke_all_sessions(session, user.id)
    session.flush()
    return user


def count_active_admins(session: Session) -> int:
    return int(
        session.execute(
            select(func.count(User.id)).where(
                User.role == UserRole.ADMIN.value, User.is_active.is_(True), User.deleted_at.is_(None)
            )
        ).scalar_one()
    )
