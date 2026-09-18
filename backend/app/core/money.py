"""Kwoty pieniężne.

W całej aplikacji pieniądze to liczby całkowite w groszach (int).
Żadnych floatów — Decimal służy wyłącznie do konwersji wejścia/wyjścia.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENTS = Decimal("0.01")


def zl_to_gr(value: str | int | float | Decimal) -> int:
    """Zamienia złotówki na grosze (zaokrąglenie połówek w górę)."""
    if isinstance(value, float):
        value = str(value)
    try:
        decimal_value = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as exc:  # pragma: no cover - obrona
        raise ValueError(f"Nieprawidłowa kwota: {value!r}") from exc
    return int((decimal_value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def gr_to_zl(grosze: int) -> Decimal:
    """Zamienia grosze na Decimal w złotych (dokładnie dwa miejsca)."""
    return (Decimal(int(grosze)) / 100).quantize(CENTS)


def format_pln(grosze: int) -> str:
    """Formatuje kwotę po polsku: 10 813,50 zł."""
    value = gr_to_zl(grosze)
    sign = "-" if value < 0 else ""
    value = abs(value)
    whole, _, fraction = f"{value:.2f}".partition(".")
    groups = []
    while len(whole) > 3:
        groups.insert(0, whole[-3:])
        whole = whole[:-3]
    groups.insert(0, whole)
    return f"{sign}{' '.join(groups)},{fraction} zł"


def percent_of(part: int, whole: int) -> Decimal:
    """Procent wykorzystania (0 gdy brak bazy)."""
    if whole <= 0:
        return Decimal("0")
    return (Decimal(part) / Decimal(whole) * 100).quantize(Decimal("0.01"))


def apply_multiplier(base_gr: int, multiplier_permille: int) -> int:
    """Mnoży kwotę przez mnożnik wyrażony w promilach (2250 = 225%).

    Mnożnik trzymamy jako liczbę całkowitą, żeby uniknąć błędów float.
    """
    return int(
        (Decimal(base_gr) * Decimal(multiplier_permille) / Decimal(1000)).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )
