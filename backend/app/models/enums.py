"""Słowniki statusów używane w modelach, schematach i interfejsie.

Wartości trzymamy w bazie jako tekst (przenośne między SQLite i PostgreSQL),
etykiety polskie żyją w słownikach LABELS i są wykorzystywane w eksportach
oraz dokumentach PDF.
"""

from __future__ import annotations

from enum import StrEnum


class PaymentStatus(StrEnum):
    UNPAID = "niezaplacone"
    PARTIAL = "czesciowo_zaplacone"
    PAID = "zaplacone"
    CANCELLED = "anulowane"
    REFUNDED = "zwrocone"


class PaymentMethod(StrEnum):
    TRANSFER = "przelew"
    CASH = "gotowka"
    CARD = "karta"
    BLIK = "blik"
    COD = "pobranie"
    MARKETPLACE = "platforma_sprzedazowa"
    OTHER = "inne"


class SalesChannel(StrEnum):
    ONLINE_SHOP = "sklep_internetowy"
    ALLEGRO = "allegro"
    DIRECT = "sprzedaz_bezposrednia"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    OTHER = "inne"


class CustomerType(StrEnum):
    B2C = "b2c"
    B2B = "b2b"


class CorrectionType(StrEnum):
    FULL_RETURN = "zwrot_calkowity"
    PARTIAL_RETURN = "zwrot_czesciowy"
    POST_SALE_DISCOUNT = "rabat_po_sprzedazy"
    CANCELLATION = "anulowanie"
    VALUE_CORRECTION = "korekta_wartosci"
    MONEY_REFUND = "zwrot_pieniedzy"


class DocumentType(StrEnum):
    RECEIPT = "rachunek"
    INVOICE_NO_VAT = "faktura_bez_vat"


class KsefStatus(StrEnum):
    NOT_APPLICABLE = "nie_dotyczy"
    OUTSIDE = "poza_ksef"
    SENT = "przeslany"


class UserRole(StrEnum):
    ADMIN = "admin"
    ACCOUNTANT = "ksiegowy"
    VIEWER = "podglad"


class AuditAction(StrEnum):
    LOGIN = "logowanie"
    LOGIN_FAILED = "nieudane_logowanie"
    LOGOUT = "wylogowanie"
    PASSWORD_CHANGE = "zmiana_hasla"
    USER_CREATE = "utworzenie_uzytkownika"
    USER_UPDATE = "zmiana_uzytkownika"
    SALE_CREATE = "dodanie_sprzedazy"
    SALE_UPDATE = "zmiana_sprzedazy"
    SALE_DELETE = "usuniecie_sprzedazy"
    PAYMENT_CREATE = "dodanie_platnosci"
    PAYMENT_DELETE = "usuniecie_platnosci"
    CORRECTION_CREATE = "korekta"
    COST_CREATE = "dodanie_kosztu"
    COST_UPDATE = "zmiana_kosztu"
    COST_DELETE = "usuniecie_kosztu"
    PRODUCT_CREATE = "dodanie_produktu"
    PRODUCT_UPDATE = "zmiana_produktu"
    PRODUCT_DELETE = "usuniecie_produktu"
    DOCUMENT_CREATE = "wystawienie_dokumentu"
    DOCUMENT_UPDATE = "zmiana_dokumentu"
    DOCUMENT_DELETE = "usuniecie_dokumentu"
    SETTINGS_UPDATE = "zmiana_ustawien"
    BACKUP_CREATE = "utworzenie_backupu"
    BACKUP_RESTORE = "przywrocenie_backupu"
    BACKUP_DELETE = "usuniecie_backupu"
    FILE_UPLOAD = "wgranie_pliku"


LABELS: dict[str, str] = {
    PaymentStatus.UNPAID: "niezapłacone",
    PaymentStatus.PARTIAL: "częściowo zapłacone",
    PaymentStatus.PAID: "zapłacone",
    PaymentStatus.CANCELLED: "anulowane",
    PaymentStatus.REFUNDED: "zwrócone",
    PaymentMethod.TRANSFER: "przelew",
    PaymentMethod.CASH: "gotówka",
    PaymentMethod.CARD: "karta",
    PaymentMethod.BLIK: "BLIK",
    PaymentMethod.COD: "pobranie",
    PaymentMethod.MARKETPLACE: "platforma sprzedażowa",
    PaymentMethod.OTHER: "inne",
    SalesChannel.ONLINE_SHOP: "sklep internetowy",
    SalesChannel.ALLEGRO: "Allegro",
    SalesChannel.DIRECT: "sprzedaż bezpośrednia",
    SalesChannel.FACEBOOK: "Facebook",
    SalesChannel.INSTAGRAM: "Instagram",
    SalesChannel.TIKTOK: "TikTok",
    SalesChannel.OTHER: "inne",
    CustomerType.B2C: "B2C",
    CustomerType.B2B: "B2B",
    CorrectionType.FULL_RETURN: "zwrot całkowity",
    CorrectionType.PARTIAL_RETURN: "zwrot częściowy",
    CorrectionType.POST_SALE_DISCOUNT: "rabat po sprzedaży",
    CorrectionType.CANCELLATION: "anulowanie zamówienia",
    CorrectionType.VALUE_CORRECTION: "korekta wartości",
    CorrectionType.MONEY_REFUND: "zwrot pieniędzy klientowi",
    DocumentType.RECEIPT: "rachunek",
    DocumentType.INVOICE_NO_VAT: "faktura bez VAT",
    KsefStatus.NOT_APPLICABLE: "nie dotyczy",
    KsefStatus.OUTSIDE: "dokument poza KSeF",
    KsefStatus.SENT: "przesłany do KSeF",
    UserRole.ADMIN: "administrator",
    UserRole.ACCOUNTANT: "księgowość",
    UserRole.VIEWER: "podgląd",
}


def label(value: str | None) -> str:
    if value is None:
        return ""
    return LABELS.get(value, value)
