"""Ewidencja, raporty, eksporty, PIT i pulpit."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import sale_payload


def przygotuj_dane(client: TestClient) -> None:
    pierwsza = client.post(
        "/api/sales",
        json=sale_payload(
            sale_date="2026-07-05",
            items=[{"name": "Formikarium", "quantity": 1, "unit_price_gr": 200_000}],
            sales_channel="allegro",
        ),
    ).json()
    client.post(
        "/api/sales/%s/payments" % pierwsza["id"],
        json={"payment_date": "2026-07-06", "amount_gr": 200_000, "method": "przelew"},
    )
    druga = client.post(
        "/api/sales",
        json=sale_payload(
            sale_date="2026-07-05",
            items=[{"name": "Terrarium", "quantity": 2, "unit_price_gr": 50_000}],
            sales_channel="sklep_internetowy",
            customer_type="b2b",
        ),
    ).json()
    client.post(
        "/api/sales/%s/payments" % druga["id"],
        json={"payment_date": "2026-08-01", "amount_gr": 40_000, "method": "blik"},
    )
    client.post(
        "/api/sales",
        json=sale_payload(
            sale_date="2026-08-11",
            items=[{"name": "Zestaw startowy", "quantity": 1, "unit_price_gr": 90_000}],
        ),
    )
    kategoria = client.get("/api/cost-categories").json()[0]
    client.post(
        "/api/costs",
        json={
            "cost_date": "2026-07-10",
            "name": "Beton",
            "category_id": kategoria["id"],
            "amount_gr": 30_000,
            "payment_method": "gotowka",
        },
    )


def test_ewidencja_sprzedazy_narastajaco(auth_client: TestClient):
    przygotuj_dane(auth_client)
    response = auth_client.get("/api/registry", params={"year": 2026, "quarter": 3})
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 3
    wiersze = body["items"]
    assert wiersze[0]["lp"] == 1
    assert [row["cumulative_gr"] for row in wiersze] == [200_000, 300_000, 390_000]
    assert body["summary"]["accrued_revenue_gr"] == 390_000
    assert wiersze[0]["payment_status"] == "zaplacone"


def test_ewidencja_dzienna(auth_client: TestClient):
    przygotuj_dane(auth_client)
    response = auth_client.get("/api/registry/daily", params={"year": 2026, "quarter": 3})
    assert response.status_code == 200
    wiersze = response.json()
    assert wiersze[0]["day"] == "2026-07-05"
    assert wiersze[0]["sales_count"] == 2
    assert wiersze[0]["total_gr"] == 300_000
    assert wiersze[-1]["cumulative_gr"] == 390_000


def test_przychod_nalezny_i_otrzymany_liczone_niezaleznie(auth_client: TestClient):
    przygotuj_dane(auth_client)
    raport = auth_client.get("/api/reports/sprzedaz_miesieczna", params={"year": 2026}).json()
    lipiec = next(row for row in raport["rows"] if row["month"] == 7)
    sierpien = next(row for row in raport["rows"] if row["month"] == 8)

    assert lipiec["accrued_gr"] == 300_000  # sprzedaż lipcowa
    assert lipiec["received_gr"] == 200_000  # tylko jedna wpłata w lipcu
    assert lipiec["costs_gr"] == 30_000
    assert sierpien["accrued_gr"] == 90_000
    assert sierpien["received_gr"] == 40_000  # wpłata do lipcowej sprzedaży


def test_raport_roczny_i_naleznosci(auth_client: TestClient):
    przygotuj_dane(auth_client)
    roczny = auth_client.get("/api/reports/sprzedaz_roczna", params={"year": 2026}).json()
    wiersz = roczny["rows"][0]
    assert wiersz["accrued_gr"] == 390_000
    assert wiersz["received_gr"] == 240_000
    assert wiersz["costs_gr"] == 30_000
    assert wiersz["income_gr"] == 210_000

    naleznosci = auth_client.get("/api/reports/naleznosci_niezaplacone", params={"year": 2026}).json()
    assert naleznosci["summary"]["outstanding_gr"] == 150_000


def test_raporty_wg_kanalu_i_produktu(auth_client: TestClient):
    przygotuj_dane(auth_client)
    kanaly = auth_client.get("/api/reports/sprzedaz_wg_kanalu", params={"year": 2026}).json()
    assert {row["channel"] for row in kanaly["rows"]} == {"allegro", "sklep_internetowy"}

    produkty = auth_client.get("/api/reports/sprzedaz_wg_produktu", params={"year": 2026}).json()
    nazwy = {row["name"] for row in produkty["rows"]}
    assert {"Formikarium", "Terrarium", "Zestaw startowy"} == nazwy


def test_eksport_raportow(auth_client: TestClient):
    przygotuj_dane(auth_client)
    csv_response = auth_client.get(
        "/api/reports/ewidencja_sprzedazy/export", params={"year": 2026, "format": "csv"}
    )
    assert csv_response.status_code == 200
    assert csv_response.content.startswith("﻿".encode("utf-8"))
    assert "Przychód należny" in csv_response.content.decode("utf-8")

    xlsx_response = auth_client.get(
        "/api/reports/sprzedaz_miesieczna/export", params={"year": 2026, "format": "xlsx"}
    )
    assert xlsx_response.status_code == 200
    assert xlsx_response.content[:2] == b"PK"

    pdf_response = auth_client.get(
        "/api/reports/sprzedaz_kwartalna/export", params={"year": 2026, "format": "pdf"}
    )
    assert pdf_response.status_code == 200
    assert pdf_response.content.startswith(b"%PDF")


def test_podsumowanie_pit(auth_client: TestClient):
    przygotuj_dane(auth_client)
    response = auth_client.get("/api/pit", params={"year": 2026})
    assert response.status_code == 200
    body = response.json()
    assert body["yearly"]["received_gr"] == 240_000
    assert body["yearly"]["costs_gr"] == 30_000
    assert body["yearly"]["income_gr"] == 210_000
    assert "PIT-36" in body["disclaimer"]
    assert len(body["monthly"]) == 12
    assert len(body["quarterly"]) == 4


def test_pulpit(auth_client: TestClient):
    przygotuj_dane(auth_client)
    response = auth_client.get("/api/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert body["limit"]["limit_gr"] == 1_081_350
    assert body["metrics"]["accrued_year_gr"] == 390_000
    assert body["metrics"]["received_year_gr"] == 240_000
    assert body["metrics"]["outstanding_gr"] == 150_000
    assert body["metrics"]["costs_year_gr"] == 30_000
    assert len(body["charts"]["last_30_days"]) == 30
    assert len(body["charts"]["monthly"]) == 12
    assert body["counters"]["ksef"]["threshold_gr"] == 1_000_000


def test_dziennik_zmian_zapisuje_operacje(auth_client: TestClient):
    przygotuj_dane(auth_client)
    response = auth_client.get("/api/audit-logs", params={"per_page": 100})
    assert response.status_code == 200
    akcje = [item["action"] for item in response.json()["items"]]
    assert "logowanie" in akcje
    assert "dodanie_sprzedazy" in akcje
    assert "dodanie_platnosci" in akcje
    assert "dodanie_kosztu" in akcje
    # W dzienniku nie zapisujemy haseł ani tokenów.
    opisy = " ".join(item["description"] or "" for item in response.json()["items"])
    assert "SuperTajne" not in opisy
