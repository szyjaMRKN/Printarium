from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    login: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    login: str
    email: str | None = None
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None = None
    must_change_password: bool = False


class SessionInfo(BaseModel):
    user: UserOut
    csrf_token: str
    expires_at: datetime


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=10, max_length=256)


class UserCreateRequest(BaseModel):
    login: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=10, max_length=256)
    email: str | None = Field(default=None, max_length=255)
    role: str = "admin"
    is_active: bool = True


class UserUpdateRequest(BaseModel):
    email: str | None = Field(default=None, max_length=255)
    role: str | None = None
    is_active: bool | None = None
    new_password: str | None = Field(default=None, min_length=10, max_length=256)
