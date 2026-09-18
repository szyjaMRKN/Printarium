"""Wspólna konfiguracja testów — każdy test dostaje własną, pustą bazę."""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "testowy-klucz-do-testow-1234567890")
os.environ.setdefault("COOKIE_SECURE", "0")
os.environ.setdefault("ADMIN_LOGIN", "")
os.environ.setdefault("ADMIN_PASSWORD", "")

from app.core.config import get_settings  # noqa: E402
from app.db.seed import seed_reference_data  # noqa: E402
from app.db.session import reset_engine, session_scope  # noqa: E402
from app.models.enums import UserRole  # noqa: E402
from app.services import auth_service  # noqa: E402
from app.services.backup_service import run_migrations  # noqa: E402

ADMIN_LOGIN = "admin"
ADMIN_PASSWORD = "SuperTajne123"


@pytest.fixture()
def environment(tmp_path, monkeypatch) -> Iterator[None]:
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("BACKUP_DIR", str(tmp_path / "backups"))
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("DATABASE_URL", "")
    get_settings.cache_clear()
    reset_engine()
    settings = get_settings()
    settings.ensure_directories()
    run_migrations()
    with session_scope() as session:
        seed_reference_data(session)
    yield
    reset_engine()
    get_settings.cache_clear()


@pytest.fixture()
def db_session(environment) -> Iterator:
    with session_scope() as session:
        yield session


@pytest.fixture()
def admin_user(environment):
    with session_scope() as session:
        user = auth_service.create_user(
            session,
            login=ADMIN_LOGIN,
            password=ADMIN_PASSWORD,
            email="admin@example.com",
            role=UserRole.ADMIN.value,
        )
        return {"id": user.id, "login": user.login}


@pytest.fixture()
def client(environment) -> Iterator[TestClient]:
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture()
def auth_client(client: TestClient, admin_user) -> TestClient:
    response = client.post(
        "/api/auth/login", json={"login": ADMIN_LOGIN, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, response.text
    client.headers.update({"X-CSRF-Token": response.json()["csrf_token"]})
    return client


def sale_payload(**overrides) -> dict:
    """Minimalna poprawna sprzedaż — kwoty w groszach."""
    payload = {
        "sale_date": date.today().isoformat(),
        "items": [{"name": "Formikarium", "quantity": 1, "unit_price_gr": 20000}],
        "discount_gr": 0,
        "shipping_gr": 0,
        "payment_method": "przelew",
        "sales_channel": "sklep_internetowy",
        "customer_type": "b2c",
    }
    payload.update(overrides)
    return payload
