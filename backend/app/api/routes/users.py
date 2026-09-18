"""Zarządzanie użytkownikami (tylko administrator)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, db_session, require_admin
from app.core.errors import ValidationError
from app.models.enums import AuditAction, UserRole
from app.models.user import User
from app.schemas.auth import UserCreateRequest, UserOut, UserUpdateRequest
from app.services import audit_service, auth_service

router = APIRouter(prefix="/users", tags=["uzytkownicy"])


@router.get("", response_model=list[UserOut])
def list_users(
    _: CurrentUser = Depends(require_admin), session: Session = Depends(db_session)
) -> list[UserOut]:
    users = session.execute(
        select(User).where(User.deleted_at.is_(None)).order_by(User.login)
    ).scalars()
    return [UserOut.model_validate(user) for user in users]


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    payload: UserCreateRequest,
    context: CurrentUser = Depends(require_admin),
    session: Session = Depends(db_session),
) -> UserOut:
    if payload.role not in {role.value for role in UserRole}:
        raise ValidationError("Nieznana rola użytkownika.")
    user = auth_service.create_user(
        session,
        login=payload.login,
        password=payload.password,
        email=payload.email,
        role=payload.role,
        is_active=payload.is_active,
    )
    audit_service.record(
        session,
        AuditAction.USER_CREATE,
        user=context.user,
        entity_type="user",
        entity_id=user.id,
        ip_address=context.ip,
        description=f"Utworzono użytkownika {user.login} (rola: {user.role}).",
    )
    session.commit()
    return UserOut.model_validate(user)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    context: CurrentUser = Depends(require_admin),
    session: Session = Depends(db_session),
) -> UserOut:
    if payload.role is not None and payload.role not in {role.value for role in UserRole}:
        raise ValidationError("Nieznana rola użytkownika.")
    target = session.get(User, user_id)
    if target is not None and target.id == context.user.id and payload.is_active is False:
        raise ValidationError("Nie możesz dezaktywować własnego konta.")
    if (
        target is not None
        and target.role == UserRole.ADMIN.value
        and (payload.is_active is False or (payload.role and payload.role != UserRole.ADMIN.value))
        and auth_service.count_active_admins(session) <= 1
    ):
        raise ValidationError("W systemie musi pozostać co najmniej jeden aktywny administrator.")

    user = auth_service.update_user(
        session,
        user_id,
        email=payload.email,
        role=payload.role,
        is_active=payload.is_active,
        new_password=payload.new_password,
    )
    audit_service.record(
        session,
        AuditAction.USER_UPDATE,
        user=context.user,
        entity_type="user",
        entity_id=user.id,
        ip_address=context.ip,
        description=f"Zmieniono użytkownika {user.login}.",
    )
    session.commit()
    return UserOut.model_validate(user)
