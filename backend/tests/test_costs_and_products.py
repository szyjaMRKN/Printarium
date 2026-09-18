"""Koszty, kategorie, załączniki i produkty."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000a4944415478da63"
    "6000000002000148afa4710000000049454e44ae426082"
)


def test_domyslne_kategorie_kosztow(auth_client: TestClient):
    response = auth_client.get("/api/cost-categories")
    assert response.status_code == 200
    nazwy = [item["name"] for item in response.json()]
    for oczekiwana in ["Materiały", "Opakowania", "Wysyłka", "Reklama", "Prowizje", "Inne"]:
        assert oczekiwana in nazwy


def test_dodanie_i_edycja_kosztu(auth_client: TestClient):
    kategoria = auth_client.get("/api/cost-categories").json()[0]
    response = auth_client.post(
        "/api/costs",
        json={
            "cost_date": "2026-09-01",
            "name": "Folia bąbelkowa",
            "category_id": kategoria["id"],
            "vendor": "Hurtownia XYZ",
            "invoice_number": "FV 12/2026",
            "amount_gr": 12300,
            "payment_method": "przelew",
        },
    )
    assert response.status_code == 201
    cost = response.json()
    assert cost["amount_gr"] == 12300
    assert cost["category_name"] == kategoria["name"]

    zmiana = auth_client.put(
        f"/api/costs/{cost['id']}",
        json={
            "cost_date": "2026-09-02",
            "name": "Folia bąbelkowa 100m",
            "category_id": kategoria["id"],
            "amount_gr": 15000,
        },
    )
    assert zmiana.status_code == 200
    assert zmiana.json()["amount_gr"] == 15000

    assert auth_client.delete(f"/api/costs/{cost['id']}").status_code == 200
    assert auth_client.get(f"/api/costs/{cost['id']}").status_code == 404


def test_wlasna_kategoria_kosztow(auth_client: TestClient):
    response = auth_client.post("/api/cost-categories", json={"name": "Żywice epoksydowe"})
    assert response.status_code == 201
    assert response.json()["slug"] == "zywice-epoksydowe"
    duplikat = auth_client.post("/api/cost-categories", json={"name": "Żywice epoksydowe"})
    assert duplikat.status_code == 409


def test_upload_zalacznika_i_pobranie(auth_client: TestClient):
    response = auth_client.post(
        "/api/attachments", files={"file": ("paragon.png", PNG_1PX, "image/png")}
    )
    assert response.status_code == 201
    attachment = response.json()
    assert attachment["original_name"] == "paragon.png"

    pobranie = auth_client.get(f"/api/attachments/{attachment['id']}")
    assert pobranie.status_code == 200
    assert pobranie.content == PNG_1PX


def test_upload_odrzuca_niedozwolone_rozszerzenie(auth_client: TestClient):
    response = auth_client.post(
        "/api/attachments", files={"file": ("zlosliwy.exe", b"MZ\x00\x00", "application/octet-stream")}
    )
    assert response.status_code == 422
    assert "rozszerzenie" in response.json()["detail"]


def test_upload_odrzuca_podmieniona_zawartosc(auth_client: TestClient):
    response = auth_client.post(
        "/api/attachments", files={"file": ("udaje.pdf", b"<script>alert(1)</script>", "application/pdf")}
    )
    assert response.status_code == 422
    assert "Zawartość pliku" in response.json()["detail"]


def test_upload_respektuje_limit_rozmiaru(auth_client: TestClient):
    assert auth_client.put("/api/settings", json={"values": {"uploads.max_size_mb": 1}}).status_code == 200
    duzy_plik = b"%PDF-" + b"0" * (1024 * 1024 + 10)
    response = auth_client.post(
        "/api/attachments", files={"file": ("duzy.pdf", duzy_plik, "application/pdf")}
    )
    assert response.status_code == 422
    assert "za duży" in response.json()["detail"]


def test_produkty_crud(auth_client: TestClient):
    response = auth_client.post(
        "/api/products",
        json={
            "name": "Formikarium Beton L",
            "sku": "FRM-L-001",
            "model": "L",
            "category": "Formikaria",
            "price_gr": 25000,
            "production_cost_gr": 9000,
        },
    )
    assert response.status_code == 201
    product = response.json()

    duplikat = auth_client.post("/api/products", json={"name": "Inne", "sku": "FRM-L-001"})
    assert duplikat.status_code == 409

    zmiana = auth_client.put(
        f"/api/products/{product['id']}",
        json={"name": "Formikarium Beton L", "sku": "FRM-L-001", "price_gr": 27000},
    )
    assert zmiana.status_code == 200
    assert zmiana.json()["price_gr"] == 27000

    lista = auth_client.get("/api/products", params={"search": "Formikarium"}).json()
    assert lista["meta"]["total"] == 1

    assert auth_client.delete(f"/api/products/{product['id']}").status_code == 200
    assert auth_client.get("/api/products").json()["meta"]["total"] == 0


def test_sprzedaz_moze_odwolywac_sie_do_produktu(auth_client: TestClient):
    product = auth_client.post(
        "/api/products", json={"name": "Terrarium S", "price_gr": 18000}
    ).json()
    response = auth_client.post(
        "/api/sales",
        json={
            "sale_date": date.today().isoformat(),
            "items": [
                {
                    "product_id": product["id"],
                    "name": "Terrarium S",
                    "quantity": 2,
                    "unit_price_gr": 18000,
                }
            ],
        },
    )
    assert response.status_code == 201
    assert response.json()["items"][0]["product_id"] == product["id"]

    nieistniejacy = auth_client.post(
        "/api/sales",
        json={
            "sale_date": date.today().isoformat(),
            "items": [{"product_id": 9999, "name": "X", "quantity": 1, "unit_price_gr": 100}],
        },
    )
    assert nieistniejacy.status_code == 422
