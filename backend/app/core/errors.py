"""Wyjątki domenowe mapowane na odpowiedzi HTTP w app/main.py."""

from __future__ import annotations


class AppError(Exception):
    """Błąd biznesowy — komunikat jest bezpieczny do pokazania użytkownikowi."""

    status_code = 400
    code = "blad_aplikacji"

    def __init__(self, message: str, *, code: str | None = None, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code


class NotFoundError(AppError):
    status_code = 404
    code = "nie_znaleziono"


class ValidationError(AppError):
    status_code = 422
    code = "blad_walidacji"


class ConflictError(AppError):
    status_code = 409
    code = "konflikt"


class AuthError(AppError):
    status_code = 401
    code = "brak_autoryzacji"


class PermissionError_(AppError):
    status_code = 403
    code = "brak_uprawnien"


class RateLimitError(AppError):
    status_code = 429
    code = "zbyt_wiele_prob"
