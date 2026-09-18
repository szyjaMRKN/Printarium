"""Limit działalności nierejestrowanej — kwartały, ostrzeżenia, przekroczenie."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import sale_payload

LIMIT_2026_GR = 1_081_350  # 225% z 4806 zł = 10 813,50 zł


def dodaj_sprzedaz(client: TestClient, kwota_gr: int, data: str) -> dict:
    response = client.post(
        "/api/sales",
        json=sale_payload(
            sale_date=data, items=[{"name": "Formikarium", "quantity": 1, "unit_price_gr": kwota_gr}]
        ),
    )
    assert response.status_code == 201, response.text
    return response.json()


def kwartal(client: TestClient, rok: int, numer: int) -> dict:
    response = client.get("/api/limits", params={"year": rok})
    assert response.status_code == 200
    return next(item for item in response.json()["quarters"] if item["quarter"] == numer)


def test_limit_domyslny_liczony_z_ustawien(auth_client: TestClient):
    response = auth_client.get("/api/limits", params={"year": 2026})
    assert response.status_code == 200
    body = response.json()
    assert body["parameters"]["minimum_wage_gr"] == 480_600
    assert body["parameters"]["limit_multiplier_permille"] == 2250
    assert body["parameters"]["quarterly_limit_gr"] == LIMIT_2026_GR


def test_scenariusz_z_wymagan_przekroczenie_limitu(auth_client: TestClient):
    # 2000 zł + 3000 zł + 4000 zł = 9000 zł przychodu należnego
    dodaj_sprzedaz(auth_client, 200_000, "2026-07-05")
    dodaj_sprzedaz(auth_client, 300_000, "2026-07-20")
    dodaj_sprzedaz(auth_client, 400_000, "2026-08-10")

    stan = kwartal(auth_client, 2026, 3)
    assert stan["accrued_revenue_gr"] == 900_000
    assert stan["limit_gr"] == LIMIT_2026_GR
    assert stan["remaining_gr"] == 181_350  # 1813,50 zł
    assert stan["status"] in ("ostrzezenie", "mocne_ostrzezenie")
    assert stan["exceedance"] is None

    # Kolejna sprzedaż 2000 zł przekracza limit.
    przekraczajaca = dodaj_sprzedaz(auth_client, 200_000, "2026-08-15")

    stan = kwartal(auth_client, 2026, 3)
    assert stan["accrued_revenue_gr"] == 1_100_000
    assert stan["status"] == "przekroczony"
    assert stan["remaining_gr"] == 0
    assert stan["message"].startswith("PRZEKROCZONO LIMIT")
    assert "CEIDG" in stan["message"]
    assert "7 dni" in stan["message"]

    exceedance = stan["exceedance"]
    assert exceedance["exceeded_on"] == "2026-08-15"
    assert exceedance["sale_id"] == przekraczajaca["id"]
    assert exceedance["sale_document_number"] == przekraczajaca["document_number"]
    assert exceedance["exceeded_by_gr"] == 1_100_000 - LIMIT_2026_GR  # 186,50 zł


def test_progi_ostrzegania(auth_client: TestClient):
    dodaj_sprzedaz(auth_client, 500_000, "2026-01-10")
    assert kwartal(auth_client, 2026, 1)["status"] == "normalny"

    dodaj_sprzedaz(auth_client, 350_000, "2026-02-10")  # 850 000 gr => ~78,6%
    stan = kwartal(auth_client, 2026, 1)
    assert stan["status"] == "ostrzezenie"
    assert stan["message"] is None

    dodaj_sprzedaz(auth_client, 150_000, "2026-03-10")  # 1 000 000 gr => ~92,5%
    stan = kwartal(auth_client, 2026, 1)
    assert stan["status"] == "mocne_ostrzezenie"
    assert stan["message"] == "UWAGA: Zbliżasz się do limitu działalności nierejestrowanej."


def test_limity_liczone_osobno_dla_kwartalow(auth_client: TestClient):
    dodaj_sprzedaz(auth_client, 1_000_000, "2026-03-31")
    dodaj_sprzedaz(auth_client, 100_000, "2026-04-01")

    assert kwartal(auth_client, 2026, 1)["accrued_revenue_gr"] == 1_000_000
    assert kwartal(auth_client, 2026, 2)["accrued_revenue_gr"] == 100_000
    assert kwartal(auth_client, 2026, 3)["accrued_revenue_gr"] == 0


def test_korekta_obniza_wykorzystanie_limitu(auth_client: TestClient):
    sale = dodaj_sprzedaz(auth_client, 900_000, "2026-02-01")
    auth_client.post(
        f"/api/sales/{sale['id']}/corrections",
        json={
            "correction_date": "2026-02-10",
            "correction_type": "zwrot_czesciowy",
            "amount_gr": 400_000,
            "reason": "Zwrot części zamówienia",
        },
    )
    assert kwartal(auth_client, 2026, 1)["accrued_revenue_gr"] == 500_000


def test_zmiana_parametrow_roku_zmienia_limit(auth_client: TestClient):
    response = auth_client.put(
        "/api/settings/fiscal-years/2026",
        json={"minimum_wage_gr": 500_000, "limit_multiplier_permille": 2250},
    )
    assert response.status_code == 200
    assert response.json()["quarterly_limit_gr"] == 1_125_000
    assert kwartal(auth_client, 2026, 1)["limit_gr"] == 1_125_000

    # Ręczne nadpisanie limitu ma pierwszeństwo.
    response = auth_client.put(
        "/api/settings/fiscal-years/2026", json={"quarterly_limit_override_gr": 1_200_000}
    )
    assert response.json()["quarterly_limit_gr"] == 1_200_000


def test_przekroczenie_nie_blokuje_kolejnych_transakcji(auth_client: TestClient):
    dodaj_sprzedaz(auth_client, 1_200_000, "2026-05-05")
    assert kwartal(auth_client, 2026, 2)["status"] == "przekroczony"
    kolejna = auth_client.post(
        "/api/sales",
        json=sale_payload(
            sale_date="2026-05-06", items=[{"name": "Kolejna", "quantity": 1, "unit_price_gr": 10000}]
        ),
    )
    assert kolejna.status_code == 201


def test_liczniki_ksef_i_kasy_fiskalnej(auth_client: TestClient):
    response = auth_client.get("/api/limits", params={"year": 2026})
    counters = response.json()["counters"]
    assert counters["ksef"]["threshold_gr"] == 1_000_000
    assert counters["cash_register"]["threshold_gr"] == 2_000_000

    dodaj_sprzedaz(auth_client, 1_900_000, "2026-06-01")  # B2C, 19 000 zł
    counters = auth_client.get("/api/limits", params={"year": 2026}).json()["counters"]
    assert counters["cash_register"]["value_gr"] == 1_900_000
    assert counters["cash_register"]["status"] == "mocne_ostrzezenie"
    assert "kasy fiskalnej" in counters["cash_register"]["message"]
