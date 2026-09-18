"""Dokumenty sprzedaży, KSeF oraz kopie zapasowe."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from tests.conftest import sale_payload


def ustaw_dane_sprzedawcy(client: TestClient) -> None:
    response = client.put(
        "/api/settings",
        json={
            "values": {
                "company.first_name": "Anna",
                "company.last_name": "Kowalska",
                "company.address": "ul. Mrówcza 7/2",
                "company.postal_code": "00-001",
                "company.city": "Warszawa",
                "company.email": "kontakt@example.com",
                "company.bank_account": "PL61109010140000071219812874",
            }
        },
    )
    assert response.status_code == 200


def test_dokument_wymaga_danych_sprzedawcy(auth_client: TestClient):
    response = auth_client.post(
        "/api/documents",
        json={
            "document_type": "rachunek",
            "issue_date": "2026-09-18",
            "buyer_name": "Jan Nowak",
            "items": [{"name": "Formikarium", "quantity": 1, "unit_price_gr": 20000}],
        },
    )
    assert response.status_code == 422
    assert "dane sprzedawcy" in response.json()["detail"]


def test_numeracja_dokumentow_miesieczna(auth_client: TestClient):
    ustaw_dane_sprzedawcy(auth_client)
    pierwszy = auth_client.post(
        "/api/documents",
        json={
            "document_type": "rachunek",
            "issue_date": "2026-09-18",
            "buyer_name": "Jan Nowak",
            "items": [{"name": "Formikarium", "quantity": 1, "unit_price_gr": 20000}],
        },
    )
    assert pierwszy.status_code == 201
    assert pierwszy.json()["number"] == "1/09/2026"

    drugi = auth_client.post(
        "/api/documents",
        json={
            "document_type": "rachunek",
            "issue_date": "2026-09-20",
            "buyer_name": "Ewa Wiśniewska",
            "items": [{"name": "Terrarium", "quantity": 1, "unit_price_gr": 30000}],
        },
    )
    assert drugi.json()["number"] == "2/09/2026"

    pazdziernik = auth_client.post(
        "/api/documents",
        json={
            "document_type": "rachunek",
            "issue_date": "2026-10-02",
            "buyer_name": "Piotr Zieliński",
            "items": [{"name": "Terrarium", "quantity": 1, "unit_price_gr": 30000}],
        },
    )
    assert pazdziernik.json()["number"] == "1/10/2026"


def test_numeracja_konfigurowalna(auth_client: TestClient):
    ustaw_dane_sprzedawcy(auth_client)
    auth_client.put(
        "/api/settings",
        json={"values": {"invoicing.number_format": "FV/{rrrr}/{nr}", "invoicing.reset_period": "year"}},
    )
    response = auth_client.post(
        "/api/documents",
        json={
            "document_type": "faktura_bez_vat",
            "issue_date": "2026-09-18",
            "buyer_name": "Firma sp. z o.o.",
            "buyer_nip": "1234563218",
            "customer_type": "b2b",
            "ksef_status": "poza_ksef",
            "items": [{"name": "Formikarium", "quantity": 3, "unit_price_gr": 20000}],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["number"] == "FV/2026/1"
    assert body["total_gr"] == 60000
    assert body["ksef_status"] == "poza_ksef"


def test_dokument_z_sprzedazy_i_pdf(auth_client: TestClient):
    ustaw_dane_sprzedawcy(auth_client)
    sale = auth_client.post(
        "/api/sales",
        json=sale_payload(
            items=[{"name": "Formikarium", "quantity": 2, "unit_price_gr": 25000}],
            shipping_gr=1990,
            customer_name="Jan Nowak",
        ),
    ).json()

    response = auth_client.post(
        "/api/documents",
        json={
            "document_type": "rachunek",
            "sale_id": sale["id"],
            "issue_date": date.today().isoformat(),
            "buyer_name": "Jan Nowak",
        },
    )
    assert response.status_code == 201
    document = response.json()
    assert document["total_gr"] == sale["total_gr"]
    assert document["seller_snapshot"]["person"] == "Anna Kowalska"

    pdf = auth_client.get(f"/api/documents/{document['id']}/pdf")
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")
    assert len(pdf.content) > 1000


def test_oznaczenie_ksef(auth_client: TestClient):
    ustaw_dane_sprzedawcy(auth_client)
    document = auth_client.post(
        "/api/documents",
        json={
            "document_type": "faktura_bez_vat",
            "issue_date": "2026-09-18",
            "buyer_name": "Firma sp. z o.o.",
            "customer_type": "b2b",
            "items": [{"name": "Formikarium", "quantity": 1, "unit_price_gr": 20000}],
        },
    ).json()

    response = auth_client.patch(
        f"/api/documents/{document['id']}",
        json={"ksef_status": "przeslany", "ksef_number": "KSEF-2026-000123"},
    )
    assert response.status_code == 200
    assert response.json()["ksef_status"] == "przeslany"
    assert response.json()["ksef_number"] == "KSEF-2026-000123"

    licznik = auth_client.get("/api/limits", params={"year": 2026}).json()["counters"]["ksef"]
    assert licznik["value_gr"] == 20000


def test_kopia_zapasowa_i_przywracanie(auth_client: TestClient):
    auth_client.post("/api/sales", json=sale_payload(document_number="PRZED-BACKUPEM"))

    utworzenie = auth_client.post("/api/backups", json={"note": "test"})
    assert utworzenie.status_code == 201
    backup = utworzenie.json()
    assert backup["filename"].startswith("backup_")
    assert backup["filename"].endswith(".sqlite3")
    assert backup["size_bytes"] > 0

    pobranie = auth_client.get(f"/api/backups/{backup['filename']}/download")
    assert pobranie.status_code == 200
    assert pobranie.content[:16].startswith(b"SQLite format 3")

    # Zmiana po wykonaniu kopii — po przywróceniu nie powinna istnieć.
    auth_client.post("/api/sales", json=sale_payload(document_number="PO-BACKUPIE"))
    assert auth_client.get("/api/sales", params={"search": "PO-BACKUPIE"}).json()["meta"]["total"] == 1

    bez_potwierdzenia = auth_client.post(
        "/api/backups/restore", json={"filename": backup["filename"], "confirm": True}
    )
    assert bez_potwierdzenia.status_code == 422

    przywrocenie = auth_client.post(
        "/api/backups/restore",
        json={"filename": backup["filename"], "confirm": True, "confirmation": "PRZYWRACAM"},
    )
    assert przywrocenie.status_code == 200
    assert przywrocenie.json()["safety_backup"].startswith("backup_")

    # Po przywróceniu sesja pochodzi z kopii — logujemy się ponownie.
    from tests.conftest import ADMIN_LOGIN, ADMIN_PASSWORD

    auth_client.cookies.clear()
    login = auth_client.post("/api/auth/login", json={"login": ADMIN_LOGIN, "password": ADMIN_PASSWORD})
    assert login.status_code == 200
    auth_client.headers.update({"X-CSRF-Token": login.json()["csrf_token"]})

    assert auth_client.get("/api/sales", params={"search": "PRZED-BACKUPEM"}).json()["meta"]["total"] == 1
    assert auth_client.get("/api/sales", params={"search": "PO-BACKUPIE"}).json()["meta"]["total"] == 0


def test_przywracanie_odrzuca_uszkodzony_plik(auth_client: TestClient):
    from app.services import backup_service

    uszkodzony = backup_service.backup_dir() / "backup_2026-01-01_00-00-00.sqlite3"
    uszkodzony.write_bytes(b"to nie jest baza danych")

    response = auth_client.post(
        "/api/backups/restore",
        json={"filename": uszkodzony.name, "confirm": True, "confirmation": "PRZYWRACAM"},
    )
    assert response.status_code in (400, 422)


def test_eksport_json(auth_client: TestClient):
    auth_client.post("/api/sales", json=sale_payload())
    response = auth_client.get("/api/backups/export-json")
    assert response.status_code == 200
    body = response.json()
    assert "sales" in body["tables"]
    assert len(body["tables"]["sales"]) == 1
    assert "users" in body["tables"]


def test_retencja_kopii(auth_client: TestClient):
    from app.services import backup_service

    assert auth_client.put("/api/settings", json={"values": {"backup.retention": 2}}).status_code == 200
    for _ in range(4):
        auth_client.post("/api/backups", json={})
    pliki = list(Path(backup_service.backup_dir()).glob("backup_*.sqlite3"))
    assert len(pliki) <= 2


def test_harmonogram_automatycznych_kopii(db_session, monkeypatch):
    """Automatyczna kopia powstaje raz dziennie po ustawionej godzinie."""
    from datetime import datetime, timedelta

    from app.core.dates import WARSAW
    from app.services import backup_service
    from app.services.settings_service import SettingsService

    SettingsService(db_session).set_many(
        {"backup.auto_enabled": True, "backup.auto_hour": 3, "backup.auto_minute": 0}
    )
    dzien = datetime(2026, 9, 18, tzinfo=WARSAW)

    # Przed godziną 3:00 nic się nie dzieje.
    assert backup_service.due_for_automatic_backup(db_session, dzien.replace(hour=2)) is False
    # Po 3:00 kopia jest należna...
    assert backup_service.due_for_automatic_backup(db_session, dzien.replace(hour=4)) is True

    backup = backup_service.create_backup(db_session, automatic=True, note="harmonogram")
    assert "_auto" in backup.filename
    # ...ale tylko raz dziennie.
    assert backup_service.due_for_automatic_backup(db_session, datetime.now(tz=WARSAW)) is False

    # Wyłączony harmonogram nie tworzy kopii.
    SettingsService(db_session).set_many({"backup.auto_enabled": False})
    jutro = datetime.now(tz=WARSAW) + timedelta(days=1)
    assert backup_service.due_for_automatic_backup(db_session, jutro) is False
