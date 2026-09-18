"""Sprzedaż, płatności częściowe, zwroty, rabaty, anulowanie i korekty."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from tests.conftest import sale_payload


def utworz_sprzedaz(client: TestClient, **overrides) -> dict:
    response = client.post("/api/sales", json=sale_payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


def test_sumy_sprzedazy_i_przychod_nalezny(auth_client: TestClient):
    sale = utworz_sprzedaz(
        auth_client,
        items=[
            {"name": "Formikarium L", "quantity": 2, "unit_price_gr": 25000},
            {"name": "Zestaw pokarmowy", "quantity": 1, "unit_price_gr": 5000},
        ],
        discount_gr=3000,
        shipping_gr=1990,
    )
    assert sale["items_total_gr"] == 55000
    assert sale["total_gr"] == 55000 - 3000 + 1990
    # Przychód należny powstaje mimo braku płatności.
    assert sale["accrued_revenue_gr"] == sale["total_gr"]
    assert sale["payment_status"] == "niezaplacone"
    assert sale["paid_amount_gr"] == 0
    assert sale["document_number"].startswith("SPR/")


def test_rabat_wiekszy_niz_wartosc_odrzucony(auth_client: TestClient):
    response = auth_client.post("/api/sales", json=sale_payload(discount_gr=999_999))
    assert response.status_code == 422
    assert "Rabat" in response.json()["detail"]


def test_platnosc_czesciowa_i_calkowita(auth_client: TestClient):
    sale = utworz_sprzedaz(auth_client, items=[{"name": "Terrarium", "quantity": 1, "unit_price_gr": 50000}])
    sale_id = sale["id"]

    pierwsza = auth_client.post(
        f"/api/sales/{sale_id}/payments",
        json={"payment_date": date.today().isoformat(), "amount_gr": 20000, "method": "blik"},
    )
    assert pierwsza.status_code == 201
    assert pierwsza.json()["payment_status"] == "czesciowo_zaplacone"
    assert pierwsza.json()["paid_amount_gr"] == 20000
    assert pierwsza.json()["outstanding_gr"] == 30000

    druga = auth_client.post(
        f"/api/sales/{sale_id}/payments",
        json={"payment_date": date.today().isoformat(), "amount_gr": 30000, "method": "przelew"},
    )
    assert druga.status_code == 201
    assert druga.json()["payment_status"] == "zaplacone"
    assert druga.json()["paid_amount_gr"] == 50000
    assert druga.json()["outstanding_gr"] == 0
    # Przychód należny nie zmienia się przez fakt zapłaty.
    assert druga.json()["accrued_revenue_gr"] == 50000


def test_platnosc_poczatkowa_przy_dodawaniu_sprzedazy(auth_client: TestClient):
    sale = utworz_sprzedaz(
        auth_client,
        items=[{"name": "Mrówki", "quantity": 1, "unit_price_gr": 12000}],
        initial_payment={"amount_gr": 12000, "payment_date": date.today().isoformat(), "method": "blik"},
    )
    assert sale["payment_status"] == "zaplacone"
    assert len(sale["payments"]) == 1


def test_data_platnosci_niezalezna_od_daty_sprzedazy(auth_client: TestClient):
    sale = utworz_sprzedaz(auth_client, sale_date="2026-03-30")
    response = auth_client.post(
        f"/api/sales/{sale['id']}/payments",
        json={"payment_date": "2026-04-05", "amount_gr": 20000, "method": "przelew"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["sale_date"] == "2026-03-30"
    assert body["last_payment_date"] == "2026-04-05"


def test_zwrot_calkowity(auth_client: TestClient):
    sale = utworz_sprzedaz(auth_client, items=[{"name": "Formikarium", "quantity": 1, "unit_price_gr": 30000}])
    auth_client.post(
        f"/api/sales/{sale['id']}/payments",
        json={"payment_date": date.today().isoformat(), "amount_gr": 30000, "method": "przelew"},
    )
    response = auth_client.post(
        f"/api/sales/{sale['id']}/corrections",
        json={
            "correction_date": date.today().isoformat(),
            "correction_type": "zwrot_calkowity",
            "refund_amount_gr": 30000,
            "refund_method": "przelew",
            "reason": "Odstąpienie od umowy",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["accrued_revenue_gr"] == 0
    assert body["corrections_total_gr"] == -30000
    assert body["paid_amount_gr"] == 0  # wpłata 30000 + zwrot -30000
    assert body["payment_status"] == "zwrocone"
    assert body["corrections"][0]["previous_value_gr"] == 30000
    assert body["corrections"][0]["new_value_gr"] == 0


def test_zwrot_czesciowy(auth_client: TestClient):
    sale = utworz_sprzedaz(auth_client, items=[{"name": "Zestaw", "quantity": 2, "unit_price_gr": 20000}])
    response = auth_client.post(
        f"/api/sales/{sale['id']}/corrections",
        json={
            "correction_date": date.today().isoformat(),
            "correction_type": "zwrot_czesciowy",
            "amount_gr": 20000,
            "reason": "Zwrot jednej sztuki",
        },
    )
    assert response.status_code == 201
    assert response.json()["accrued_revenue_gr"] == 20000
    assert response.json()["corrections_total_gr"] == -20000


def test_rabat_po_sprzedazy(auth_client: TestClient):
    sale = utworz_sprzedaz(auth_client, items=[{"name": "Terrarium", "quantity": 1, "unit_price_gr": 40000}])
    response = auth_client.post(
        f"/api/sales/{sale['id']}/corrections",
        json={
            "correction_date": date.today().isoformat(),
            "correction_type": "rabat_po_sprzedazy",
            "amount_gr": 5000,
            "reason": "Rekompensata za opóźnienie",
        },
    )
    assert response.status_code == 201
    assert response.json()["accrued_revenue_gr"] == 35000


def test_korekta_wartosci(auth_client: TestClient):
    sale = utworz_sprzedaz(auth_client, items=[{"name": "Terrarium", "quantity": 1, "unit_price_gr": 40000}])
    response = auth_client.post(
        f"/api/sales/{sale['id']}/corrections",
        json={
            "correction_date": date.today().isoformat(),
            "correction_type": "korekta_wartosci",
            "new_value_gr": 45000,
            "reason": "Doliczenie dodatkowej pozycji",
        },
    )
    assert response.status_code == 201
    assert response.json()["accrued_revenue_gr"] == 45000
    assert response.json()["corrections"][0]["amount_gr"] == 5000


def test_anulowanie_zamowienia(auth_client: TestClient):
    sale = utworz_sprzedaz(auth_client)
    response = auth_client.post(
        f"/api/sales/{sale['id']}/corrections",
        json={
            "correction_date": date.today().isoformat(),
            "correction_type": "anulowanie",
            "reason": "Klient zrezygnował",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["is_cancelled"] is True
    assert body["accrued_revenue_gr"] == 0
    assert body["payment_status"] == "anulowane"

    # Anulowanej sprzedaży nie edytujemy — tylko korekty.
    zmiana = auth_client.put(f"/api/sales/{sale['id']}", json=sale_payload())
    assert zmiana.status_code == 409


def test_zwrot_pieniedzy_nie_zmienia_przychodu_naleznego(auth_client: TestClient):
    sale = utworz_sprzedaz(auth_client, items=[{"name": "Zestaw", "quantity": 1, "unit_price_gr": 30000}])
    auth_client.post(
        f"/api/sales/{sale['id']}/payments",
        json={"payment_date": date.today().isoformat(), "amount_gr": 30000, "method": "przelew"},
    )
    response = auth_client.post(
        f"/api/sales/{sale['id']}/corrections",
        json={
            "correction_date": date.today().isoformat(),
            "correction_type": "zwrot_pieniedzy",
            "refund_amount_gr": 10000,
            "reason": "Częściowy zwrot kosztów wysyłki",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["accrued_revenue_gr"] == 30000
    assert body["paid_amount_gr"] == 20000


def test_zwrot_wiekszy_niz_wplaty_odrzucony(auth_client: TestClient):
    sale = utworz_sprzedaz(auth_client)
    response = auth_client.post(
        f"/api/sales/{sale['id']}/corrections",
        json={
            "correction_date": date.today().isoformat(),
            "correction_type": "zwrot_pieniedzy",
            "refund_amount_gr": 5000,
        },
    )
    assert response.status_code == 422


def test_edycja_sprzedazy_przelicza_sumy(auth_client: TestClient):
    sale = utworz_sprzedaz(auth_client)
    payload = sale_payload(
        items=[{"name": "Formikarium XL", "quantity": 3, "unit_price_gr": 30000}], shipping_gr=2000
    )
    response = auth_client.put(f"/api/sales/{sale['id']}", json=payload)
    assert response.status_code == 200
    assert response.json()["total_gr"] == 92000
    assert response.json()["accrued_revenue_gr"] == 92000


def test_usuwanie_jest_miekkie_i_odwracalne(auth_client: TestClient):
    sale = utworz_sprzedaz(auth_client)
    assert auth_client.delete(f"/api/sales/{sale['id']}?reason=pomylka").status_code == 200
    assert auth_client.get(f"/api/sales/{sale['id']}").status_code == 404
    assert auth_client.post(f"/api/sales/{sale['id']}/restore").status_code == 200
    assert auth_client.get(f"/api/sales/{sale['id']}").status_code == 200


def test_filtrowanie_i_wyszukiwanie(auth_client: TestClient):
    utworz_sprzedaz(auth_client, sale_date="2026-01-15", sales_channel="allegro", customer_type="b2b")
    utworz_sprzedaz(auth_client, sale_date="2026-05-20", sales_channel="sklep_internetowy")

    kwartal = auth_client.get("/api/sales", params={"year": 2026, "quarter": 1}).json()
    assert kwartal["meta"]["total"] == 1

    kanal = auth_client.get("/api/sales", params={"sales_channel": "allegro"}).json()
    assert kanal["meta"]["total"] == 1

    b2b = auth_client.get("/api/sales", params={"customer_type": "b2b"}).json()
    assert b2b["meta"]["total"] == 1

    szukaj = auth_client.get("/api/sales", params={"search": "Formikarium"}).json()
    assert szukaj["meta"]["total"] == 2


def test_numer_dokumentu_musi_byc_unikalny(auth_client: TestClient):
    utworz_sprzedaz(auth_client, document_number="ZAM/1")
    response = auth_client.post("/api/sales", json=sale_payload(document_number="ZAM/1"))
    assert response.status_code == 409
