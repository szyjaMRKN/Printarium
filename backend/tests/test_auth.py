"""Logowanie, sesja, uprawnienia i limit prób."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import ADMIN_LOGIN, ADMIN_PASSWORD, sale_payload


def test_logowanie_i_sesja(client: TestClient, admin_user):
    response = client.post("/api/auth/login", json={"login": ADMIN_LOGIN, "password": ADMIN_PASSWORD})
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["login"] == ADMIN_LOGIN
    assert data["csrf_token"]

    cookies = response.headers.get_list("set-cookie")
    session_cookie = next(cookie for cookie in cookies if cookie.startswith("ewid_session="))
    assert "HttpOnly" in session_cookie
    assert "SameSite=lax" in session_cookie.replace("samesite", "SameSite")

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["user"]["login"] == ADMIN_LOGIN


def test_bledne_haslo_nie_loguje(client: TestClient, admin_user):
    response = client.post("/api/auth/login", json={"login": ADMIN_LOGIN, "password": "zle-haslo"})
    assert response.status_code == 401
    assert "Nieprawidłowy login lub hasło." in response.json()["detail"]


def test_brak_sesji_blokuje_api(client: TestClient):
    assert client.get("/api/sales").status_code == 401
    assert client.get("/api/dashboard").status_code == 401


def test_limit_prob_logowania(client: TestClient, admin_user):
    for _ in range(5):
        client.post("/api/auth/login", json={"login": ADMIN_LOGIN, "password": "zle"})
    response = client.post("/api/auth/login", json={"login": ADMIN_LOGIN, "password": ADMIN_PASSWORD})
    assert response.status_code == 429
    assert "Zbyt wiele" in response.json()["detail"]


def test_csrf_wymagany_przy_zapisie(auth_client: TestClient):
    bez_tokenu = auth_client.post("/api/sales", json=sale_payload(), headers={"X-CSRF-Token": ""})
    assert bez_tokenu.status_code == 403
    zly_token = auth_client.post("/api/sales", json=sale_payload(), headers={"X-CSRF-Token": "podrobiony"})
    assert zly_token.status_code == 403
    poprawny = auth_client.post("/api/sales", json=sale_payload())
    assert poprawny.status_code == 201


def test_wylogowanie_unieważnia_sesje(auth_client: TestClient):
    assert auth_client.post("/api/auth/logout").status_code == 200
    assert auth_client.get("/api/auth/me").status_code == 401


def test_zmiana_hasla(auth_client: TestClient, client: TestClient):
    response = auth_client.post(
        "/api/auth/password",
        json={"current_password": ADMIN_PASSWORD, "new_password": "NoweHaslo9876"},
    )
    assert response.status_code == 200
    auth_client.cookies.clear()
    stare = client.post("/api/auth/login", json={"login": ADMIN_LOGIN, "password": ADMIN_PASSWORD})
    assert stare.status_code == 401
    nowe = client.post("/api/auth/login", json={"login": ADMIN_LOGIN, "password": "NoweHaslo9876"})
    assert nowe.status_code == 200


def test_slabe_haslo_odrzucone(auth_client: TestClient):
    response = auth_client.post(
        "/api/auth/password", json={"current_password": ADMIN_PASSWORD, "new_password": "słabehasło"}
    )
    assert response.status_code == 422


def test_uzytkownik_nieaktywny_nie_zaloguje(auth_client: TestClient, client: TestClient):
    utworzony = auth_client.post(
        "/api/users",
        json={"login": "ksiegowa", "password": "TajneHaslo123", "role": "ksiegowy"},
    )
    assert utworzony.status_code == 201
    user_id = utworzony.json()["id"]
    assert auth_client.patch(f"/api/users/{user_id}", json={"is_active": False}).status_code == 200

    response = client.post("/api/auth/login", json={"login": "ksiegowa", "password": "TajneHaslo123"})
    assert response.status_code == 401
    assert "nieaktywne" in response.json()["detail"]


def test_rola_podglad_nie_moze_zapisywac(auth_client: TestClient, client: TestClient):
    auth_client.post(
        "/api/users", json={"login": "obserwator", "password": "TajneHaslo123", "role": "podglad"}
    )
    viewer = TestClient(client.app)
    login = viewer.post("/api/auth/login", json={"login": "obserwator", "password": "TajneHaslo123"})
    assert login.status_code == 200
    viewer.headers.update({"X-CSRF-Token": login.json()["csrf_token"]})
    assert viewer.get("/api/sales").status_code == 200
    assert viewer.post("/api/sales", json=sale_payload()).status_code == 403


def test_health_dostepny_bez_logowania(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["version"]
