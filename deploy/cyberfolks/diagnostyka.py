# -*- coding: utf-8 -*-
"""Diagnostyka wdrożenia na hostingu współdzielonym — bez dostępu SSH.

Skrypt uruchamiasz z panelu: *Aplikacje Python → Wykonaj skrypt Python*,
podając ścieżkę `diagnostyka.py` (albo pełną, np.
`/home/UŻYTKOWNIK/ewidencja/diagnostyka.py`).

Raport zapisuje się obok skryptu jako `diagnostyka.txt` — otwórz go
w menedżerze plików. Wartości z `.env` nie trafiają do raportu, wypisywane
są wyłącznie nazwy ustawionych zmiennych.

Celowo napisany pod stary Python (3.6+), żeby zadziałał także wtedy, gdy
aplikacja ma jeszcze ustawioną wersję 3.8 i sama nie startuje.
"""

from __future__ import print_function

import io
import os
import sys
import traceback

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
RAPORT = os.path.join(APP_ROOT, "diagnostyka.txt")

linie = []


def wypisz(tekst=""):
    linie.append(tekst)


def naglowek(tytul):
    wypisz("")
    wypisz("=" * 70)
    wypisz(tytul)
    wypisz("=" * 70)


def czytaj_plik(sciezka, limit=8000):
    try:
        with io.open(sciezka, "r", encoding="utf-8", errors="replace") as uchwyt:
            tresc = uchwyt.read(limit)
        return tresc
    except Exception as blad:
        return "!! nie udało się odczytać: %s" % (blad,)


def listuj(katalog, poziom=0, maks_poziom=1):
    if not os.path.isdir(katalog):
        wypisz("%s!! brak katalogu: %s" % ("  " * poziom, katalog))
        return
    try:
        pozycje = sorted(os.listdir(katalog))
    except Exception as blad:
        wypisz("%s!! brak dostępu: %s" % ("  " * poziom, blad))
        return
    for nazwa in pozycje:
        pelna = os.path.join(katalog, nazwa)
        wciecie = "  " * (poziom + 1)
        if os.path.isdir(pelna):
            wypisz("%s%s/" % (wciecie, nazwa))
            if poziom < maks_poziom:
                listuj(pelna, poziom + 1, maks_poziom)
        else:
            try:
                rozmiar = os.path.getsize(pelna)
            except Exception:
                rozmiar = -1
            wypisz("%s%s  (%s B)" % (wciecie, nazwa, rozmiar))


# --------------------------------------------------------------------------
naglowek("1. ŚRODOWISKO")
wypisz("Wersja Pythona:    %s" % (sys.version.replace("\n", " "),))
wypisz("Interpreter:       %s" % (sys.executable,))
wypisz("Katalog aplikacji: %s" % (APP_ROOT,))
wypisz("Katalog roboczy:   %s" % (os.getcwd(),))
wypisz("Katalog domowy:    %s" % (os.path.expanduser("~"),))
if sys.version_info < (3, 11):
    wypisz("")
    wypisz(">>> UWAGA: aplikacja wymaga Pythona 3.11 lub nowszego.")
    wypisz(">>> Zmień wersję w panelu i uruchom ponownie instalację zależności.")

# --------------------------------------------------------------------------
naglowek("2. PLIKI APLIKACJI")
listuj(APP_ROOT, maks_poziom=1)

# --------------------------------------------------------------------------
naglowek("3. KONFIGURACJA (.env)")
sciezka_env = os.path.join(APP_ROOT, ".env")
sciezka_wzor = os.path.join(APP_ROOT, ".env.przyklad")
wypisz(".env            : %s" % ("jest" if os.path.isfile(sciezka_env) else "BRAK"))
wypisz(".env.przyklad   : %s" % ("jest" if os.path.isfile(sciezka_wzor) else "brak"))
if os.path.isfile(sciezka_env):
    wypisz("")
    wypisz("Ustawione zmienne (bez wartości):")
    for wiersz in czytaj_plik(sciezka_env).splitlines():
        wiersz = wiersz.strip()
        if not wiersz or wiersz.startswith("#") or "=" not in wiersz:
            continue
        klucz, wartosc = wiersz.split("=", 1)
        stan = "ustawione" if wartosc.strip() else "puste"
        wypisz("  %-20s %s" % (klucz.strip(), stan))
elif os.path.isfile(sciezka_wzor):
    wypisz("")
    wypisz(">>> Plik nadal nazywa się .env.przyklad — zmień nazwę na .env.")

# --------------------------------------------------------------------------
naglowek("4. KATALOG W DOMENIE I REGUŁY .HTACCESS")


def znajdz_public_html():
    """Typowe miejsca katalogów publicznych, a w ostateczności przeszukanie."""
    dom_uzytkownika = os.path.expanduser("~")
    znalezione = []
    katalog_domen = os.path.join(dom_uzytkownika, "domains")
    if os.path.isdir(katalog_domen):
        try:
            for domena in sorted(os.listdir(katalog_domen)):
                kandydat = os.path.join(katalog_domen, domena, "public_html")
                if os.path.isdir(kandydat):
                    znalezione.append(kandydat)
        except Exception:
            pass
    wlasny = os.path.join(dom_uzytkownika, "public_html")
    if os.path.isdir(wlasny):
        znalezione.append(wlasny)
    if znalezione:
        return znalezione
    # Nietypowy układ katalogów — szukamy płytko, żeby nie przeczesywać całego konta.
    for katalog, podkatalogi, _pliki in os.walk(dom_uzytkownika):
        glebokosc = katalog[len(dom_uzytkownika):].count(os.sep)
        if glebokosc >= 3:
            podkatalogi[:] = []
            continue
        if "public_html" in podkatalogi:
            znalezione.append(os.path.join(katalog, "public_html"))
    return znalezione


nazwa_aplikacji = os.path.basename(APP_ROOT)
katalogi_publiczne = znajdz_public_html()
if not katalogi_publiczne:
    wypisz(">>> Nie znalazłem żadnego katalogu public_html.")

htaccess_aplikacji_istnieje = False
for public_html in katalogi_publiczne:
    wypisz("")
    wypisz("--- %s ---" % (public_html,))
    wypisz("zawartość:")
    listuj(public_html, maks_poziom=0)
    katalog_aplikacji = os.path.join(public_html, nazwa_aplikacji)
    wypisz("")
    wypisz("katalog /%s : %s" % (nazwa_aplikacji, "jest" if os.path.isdir(katalog_aplikacji) else "BRAK"))
    if os.path.isdir(katalog_aplikacji):
        listuj(katalog_aplikacji, maks_poziom=0)
        htaccess_aplikacji = os.path.join(katalog_aplikacji, ".htaccess")
        wypisz("")
        wypisz(".htaccess aplikacji:")
        if os.path.isfile(htaccess_aplikacji):
            htaccess_aplikacji_istnieje = True
            wypisz(czytaj_plik(htaccess_aplikacji))
        else:
            wypisz(">>> BRAK — bez niego Passenger nie obsługuje tego adresu.")
    htaccess_domeny = os.path.join(public_html, ".htaccess")
    wypisz("")
    wypisz(".htaccess domeny:")
    if os.path.isfile(htaccess_domeny):
        wypisz(czytaj_plik(htaccess_domeny))
    else:
        wypisz("(brak pliku)")

# --------------------------------------------------------------------------
naglowek("5. ZAINSTALOWANE ZALEŻNOŚCI")
for nazwa_modulu in ("fastapi", "starlette", "pydantic", "sqlalchemy", "alembic", "a2wsgi", "argon2", "reportlab", "openpyxl"):
    try:
        modul = __import__(nazwa_modulu)
        wersja = getattr(modul, "__version__", "?")
        wypisz("  %-12s %s" % (nazwa_modulu, wersja))
    except Exception as blad:
        wypisz("  %-12s BRAK (%s)" % (nazwa_modulu, blad))

# --------------------------------------------------------------------------
naglowek("6. PRÓBA URUCHOMIENIA APLIKACJI")
aplikacja = None
try:
    if APP_ROOT not in sys.path:
        sys.path.insert(0, APP_ROOT)
    import passenger_wsgi

    aplikacja = passenger_wsgi.application
    wypisz("Import passenger_wsgi: OK (migracje i dane startowe wykonane)")
except Exception:
    wypisz("Import passenger_wsgi: BŁĄD")
    wypisz(traceback.format_exc())

if aplikacja is not None:
    def zapytaj(sciezka):
        """Żądanie wykonane wewnątrz procesu — bez udziału serwera WWW."""
        srodowisko = {
            "REQUEST_METHOD": "GET",
            "SCRIPT_NAME": "",
            "PATH_INFO": sciezka,
            "QUERY_STRING": "",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "80",
            "SERVER_PROTOCOL": "HTTP/1.1",
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": "http",
            "wsgi.input": io.BytesIO(b""),
            "wsgi.errors": sys.stderr,
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
        }
        wynik = {}

        def start_response(status, naglowki, exc_info=None):
            wynik["status"] = status
            return lambda dane: None

        try:
            tresc = b"".join(aplikacja(srodowisko, start_response))
            return wynik.get("status", "?"), tresc[:200]
        except Exception:
            return "WYJĄTEK", traceback.format_exc()[-800:].encode("utf-8", "replace")

    for sciezka in ("/health", "/"):
        status, poczatek = zapytaj(sciezka)
        wypisz("")
        wypisz("GET %s -> %s" % (sciezka, status))
        wypisz("  %s" % (poczatek.decode("utf-8", "replace").replace("\n", " ")[:200],))

# --------------------------------------------------------------------------
naglowek("7. LOG BŁĘDÓW")
znaleziono_log = False
for nazwa_logu in ("stderr.log", "passenger.log", "error.log"):
    sciezka_logu = os.path.join(APP_ROOT, nazwa_logu)
    if os.path.isfile(sciezka_logu):
        znaleziono_log = True
        wypisz("--- %s (ostatnie 60 linii) ---" % (nazwa_logu,))
        wiersze = czytaj_plik(sciezka_logu, limit=200000).splitlines()
        for wiersz in wiersze[-60:]:
            wypisz(wiersz)
if not znaleziono_log:
    wypisz("(brak plików z logami w katalogu aplikacji)")

# --------------------------------------------------------------------------
naglowek("8. WNIOSEK")
if sys.version_info < (3, 11):
    wypisz("Wersja Pythona jest za stara — najpierw zmień ją w panelu na 3.11+,")
    wypisz("powtórz instalację zależności i uruchom tę diagnostykę ponownie.")
elif aplikacja is None:
    wypisz("Aplikacja nie daje się uruchomić — przyczyna jest w sekcji 6 (ślad błędu).")
elif not htaccess_aplikacji_istnieje:
    wypisz("Aplikacja działa poprawnie wewnątrz serwera, ale w katalogu domeny brakuje")
    wypisz("pliku .htaccess Passengera — dlatego żądania obsługuje WordPress.")
    wypisz("Sprawdź w panelu pole 'URL aplikacji' i zapisz ustawienia ponownie.")
else:
    wypisz("Aplikacja działa wewnątrz serwera i katalog w domenie ma .htaccess,")
    wypisz("więc problem leży w kolejności reguł .htaccess (sekcja 4) — reguły")
    wypisz("WordPressa przechwytują adresy aplikacji, zanim trafią do Passengera.")

# --------------------------------------------------------------------------
raport = "\n".join(linie) + "\n"
try:
    with io.open(RAPORT, "w", encoding="utf-8") as uchwyt:
        uchwyt.write(raport)
    koncowka = "\nRaport zapisany: %s\n" % (RAPORT,)
except Exception as blad:
    koncowka = "\nNie udało się zapisać raportu (%s) — skopiuj wydruk powyżej.\n" % (blad,)

print(raport)
print(koncowka)
