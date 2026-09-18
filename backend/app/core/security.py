"""Hasła, tokeny sesji i CSRF."""

from __future__ import annotations

import hashlib
import hmac
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from argon2.low_level import Type

# Argon2id — parametry świadomie umiarkowane, aplikacja działa na małym VPS.
_hasher = PasswordHasher(time_cost=3, memory_cost=64 * 1024, parallelism=2, hash_len=32, salt_len=16, type=Type.ID)

MIN_PASSWORD_LENGTH = 10


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    try:
        return _hasher.check_needs_rehash(password_hash)
    except InvalidHashError:  # pragma: no cover - uszkodzony hash
        return True


def generate_token(length: int = 48) -> str:
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """Tokeny sesji trzymamy w bazie wyłącznie jako skrót SHA-256."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def constant_time_compare(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))


def password_problems(password: str) -> list[str]:
    """Minimalne wymagania hasła — walidacja po stronie backendu."""
    problems: list[str] = []
    if len(password) < MIN_PASSWORD_LENGTH:
        problems.append(f"Hasło musi mieć co najmniej {MIN_PASSWORD_LENGTH} znaków.")
    if password.lower() == password or password.upper() == password:
        problems.append("Hasło musi zawierać małe i wielkie litery.")
    if not any(char.isdigit() for char in password):
        problems.append("Hasło musi zawierać co najmniej jedną cyfrę.")
    return problems
