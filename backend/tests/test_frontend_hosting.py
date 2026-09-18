"""Serwowanie frontendu przez backend — wariant hostingu współdzielonego.

Tam nie ma osobnego serwera plików statycznych: powłokę aplikacji i API
wystawia ten sam proces, dodatkowo podpięty w podkatalogu domeny.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.session import reset_engine


@pytest.fixture()
def frontend_client(tmp_path, monkeypatch, environment) -> Iterator[TestClient]:
    frontend = tmp_path / "frontend"
    (frontend / "assets").mkdir(parents=True)
    (frontend / "index.html").write_text("<!doctype html><title>Ewidencja</title>", encoding="utf-8")
    (frontend / "assets" / "index-abc123.js").write_text("console.log('ewidencja');", encoding="utf-8")
    (frontend / "sw.js").write_text("/* service worker */", encoding="utf-8")

    monkeypatch.setenv("FRONTEND_DIR", str(frontend))
    get_settings.cache_clear()
    reset_engine()

    from app.main import create_app

    with TestClient(create_app()) as client:
        yield client

    get_settings.cache_clear()
    reset_engine()


def test_powloka_aplikacji_jest_serwowana(frontend_client: TestClient) -> None:
    response = frontend_client.get("/")
    assert response.status_code == 200
    assert "Ewidencja" in response.text
    # Powłoka nie może się cache'ować, inaczej aktualizacja nie dotrze do przeglądarki.
    assert response.headers["cache-control"] == "no-cache"


def test_nieznana_sciezka_dostaje_index_html(frontend_client: TestClient) -> None:
    """Routing SPA działa po odświeżeniu strony na dowolnym adresie."""
    response = frontend_client.get("/sprzedaz/nowa")
    assert response.status_code == 200
    assert "Ewidencja" in response.text


def test_nieistniejace_api_zwraca_404(frontend_client: TestClient) -> None:
    """Adresy API nie mogą wpadać w awaryjny index.html."""
    response = frontend_client.get("/api/nie-ma-takiego-zasobu")
    assert response.status_code == 404


def test_api_dziala_obok_frontendu(frontend_client: TestClient) -> None:
    response = frontend_client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.headers["content-security-policy"].startswith("default-src 'none'")


def test_pliki_z_hashem_cachuja_sie_na_stale(frontend_client: TestClient) -> None:
    response = frontend_client.get("/assets/index-abc123.js")
    assert response.status_code == 200
    assert "immutable" in response.headers["cache-control"]


def test_powloka_ma_lagodniejsza_polityke_csp(frontend_client: TestClient) -> None:
    """Skrypty i style aplikacji muszą się wykonać, API zostaje bez uprawnień."""
    csp = frontend_client.get("/").headers["content-security-policy"]
    assert "script-src 'self'" in csp


def test_aplikacja_w_podkatalogu_domeny(tmp_path, monkeypatch, environment) -> None:
    """Pod Passengerem aplikacja bywa podpięta pod /ewidencja (root_path).

    Serwer przekazuje przedrostek w SCRIPT_NAME, a most a2wsgi wystawia go
    jako `root_path` — trasy muszą pasować mimo dłuższego adresu.
    """
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "index.html").write_text("<!doctype html><title>Ewidencja</title>", encoding="utf-8")
    monkeypatch.setenv("FRONTEND_DIR", str(frontend))
    get_settings.cache_clear()
    reset_engine()

    from app.main import create_app

    with TestClient(create_app(), root_path="/ewidencja") as client:
        assert client.get("/ewidencja/health").status_code == 200
        assert client.get("/ewidencja/api/auth/me").status_code == 401
        powloka = client.get("/ewidencja/sprzedaz")
        assert powloka.status_code == 200
        assert "Ewidencja" in powloka.text

    get_settings.cache_clear()
    reset_engine()
