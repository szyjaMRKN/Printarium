"""Testy jednostkowe warstwy kwot i dat."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.core.dates import quarter_of, quarter_range
from app.core.money import apply_multiplier, format_pln, gr_to_zl, percent_of, zl_to_gr


def test_zl_to_gr_bez_bledow_zaokraglen():
    assert zl_to_gr("10813.50") == 1_081_350
    assert zl_to_gr("0.1") + zl_to_gr("0.2") == zl_to_gr("0.3")
    assert zl_to_gr(Decimal("4806")) == 480_600


def test_gr_to_zl_i_format():
    assert gr_to_zl(1_081_350) == Decimal("10813.50")
    assert format_pln(1_081_350) == "10 813,50 zł"
    assert format_pln(-2550) == "-25,50 zł"
    assert format_pln(0) == "0,00 zł"


def test_limit_kwartalny_liczony_z_mnoznika():
    # 225% minimalnego wynagrodzenia 4806 zł = 10 813,50 zł
    assert apply_multiplier(480_600, 2250) == 1_081_350


def test_percent_of():
    assert percent_of(785_000, 1_081_350) == Decimal("72.59")
    assert percent_of(100, 0) == Decimal("0")


def test_kwartaly():
    assert quarter_of(date(2026, 1, 1)) == 1
    assert quarter_of(date(2026, 3, 31)) == 1
    assert quarter_of(date(2026, 4, 1)) == 2
    assert quarter_of(date(2026, 9, 18)) == 3
    assert quarter_of(date(2026, 12, 31)) == 4
    assert quarter_range(2026, 1) == (date(2026, 1, 1), date(2026, 3, 31))
    assert quarter_range(2026, 2) == (date(2026, 4, 1), date(2026, 6, 30))
    assert quarter_range(2026, 3) == (date(2026, 7, 1), date(2026, 9, 30))
    assert quarter_range(2026, 4) == (date(2026, 10, 1), date(2026, 12, 31))
