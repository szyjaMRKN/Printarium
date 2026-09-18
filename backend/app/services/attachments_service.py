"""Załączniki: bezpieczny zapis plików poza katalogiem WWW.

Nazwa pliku na dysku jest losowa, rozszerzenie i typ MIME są weryfikowane,
a zawartość dodatkowo sprawdzana po sygnaturze bajtowej.
"""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dates import utcnow
from app.core.errors import NotFoundError, ValidationError
from app.models.attachment import Attachment
from app.models.enums import AuditAction
from app.models.user import User
from app.services import audit_service
from app.services.settings_service import SettingsService

ALLOWED_MIME: dict[str, set[str]] = {
    "pdf": {"application/pdf"},
    "jpg": {"image/jpeg"},
    "jpeg": {"image/jpeg"},
    "png": {"image/png"},
    "webp": {"image/webp"},
}

MAGIC_PREFIXES: dict[str, tuple[bytes, ...]] = {
    "pdf": (b"%PDF-",),
    "jpg": (b"\xff\xd8\xff",),
    "jpeg": (b"\xff\xd8\xff",),
    "png": (b"\x89PNG\r\n\x1a\n",),
    "webp": (b"RIFF",),
}


def upload_dir() -> Path:
    directory = get_settings().upload_dir
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _extension(filename: str) -> str:
    suffix = Path(filename or "").suffix.lower().lstrip(".")
    return suffix


def validate_upload(session: Session, filename: str, content_type: str, content: bytes) -> str:
    settings_service = SettingsService(session)
    allowed = {str(ext).lower() for ext in settings_service.get("uploads.allowed_extensions")}
    max_bytes = settings_service.get_int("uploads.max_size_mb") * 1024 * 1024

    extension = _extension(filename)
    if extension not in allowed:
        raise ValidationError(
            "Niedozwolone rozszerzenie pliku. Dozwolone: " + ", ".join(sorted(allowed)) + "."
        )
    if len(content) == 0:
        raise ValidationError("Plik jest pusty.")
    if len(content) > max_bytes:
        raise ValidationError(
            f"Plik jest za duży. Maksymalny rozmiar to {settings_service.get_int('uploads.max_size_mb')} MB."
        )
    expected_mimes = ALLOWED_MIME.get(extension, set())
    if content_type and expected_mimes and content_type.split(";")[0].strip() not in expected_mimes:
        raise ValidationError("Typ MIME pliku nie zgadza się z jego rozszerzeniem.")
    prefixes = MAGIC_PREFIXES.get(extension)
    if prefixes and not any(content.startswith(prefix) for prefix in prefixes):
        raise ValidationError("Zawartość pliku nie odpowiada deklarowanemu formatowi.")
    if extension == "webp" and content[8:12] != b"WEBP":
        raise ValidationError("Zawartość pliku nie odpowiada deklarowanemu formatowi.")
    return extension


def store_upload(
    session: Session,
    *,
    filename: str,
    content_type: str,
    content: bytes,
    user: User | None,
    ip: str | None = None,
) -> Attachment:
    extension = validate_upload(session, filename, content_type, content)
    stored_name = f"{uuid.uuid4().hex}.{extension}"
    target = upload_dir() / stored_name
    target.write_bytes(content)
    try:
        target.chmod(0o600)
    except OSError:  # pragma: no cover - systemy plików bez uprawnień POSIX
        pass

    attachment = Attachment(
        stored_name=stored_name,
        original_name=Path(filename).name[:255],
        content_type=(content_type or "application/octet-stream")[:100],
        size_bytes=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
        uploaded_by_id=user.id if user else None,
    )
    session.add(attachment)
    session.flush()
    audit_service.record(
        session,
        AuditAction.FILE_UPLOAD,
        user=user,
        entity_type="attachment",
        entity_id=attachment.id,
        ip_address=ip,
        description=f"Wgrano plik {attachment.original_name} ({attachment.size_bytes} B).",
    )
    return attachment


def get_attachment(session: Session, attachment_id: int) -> Attachment:
    attachment = session.get(Attachment, attachment_id)
    if attachment is None or attachment.deleted_at is not None:
        raise NotFoundError("Nie znaleziono załącznika.")
    return attachment


def attachment_path(attachment: Attachment) -> Path:
    path = upload_dir() / attachment.stored_name
    # Obrona przed próbą wyjścia poza katalog uploadów.
    if path.parent.resolve() != upload_dir().resolve():
        raise NotFoundError("Nie znaleziono pliku załącznika.")
    if not path.exists():
        raise NotFoundError("Plik załącznika nie istnieje na dysku.")
    return path


def soft_delete(session: Session, attachment_id: int, user: User | None) -> Attachment:
    attachment = get_attachment(session, attachment_id)
    attachment.deleted_at = utcnow()
    session.flush()
    return attachment
