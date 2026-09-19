# Ewidencja działalności nierejestrowanej

Panel księgowo-sprzedażowy dla polskiej **działalności nierejestrowanej**: sprzedaż,
płatności, korekty, koszty, dokumenty, raporty, limity i kopie zapasowe.
Aplikacja działa w przeglądarce, wszystkie dane trzymasz na własnym serwerze w bazie
SQLite. Interfejs i dokumenty są po polsku, waluta PLN, daty w formacie `DD.MM.RRRR`,
strefa czasowa `Europe/Warsaw`.

> To repozytorium zawiera także motyw WooCommerce „Printarium” (katalog `printarium/`).
> Jego dokumentacja: [`docs-motyw-printarium.md`](docs-motyw-printarium.md).

---

## Spis treści

1. [Co potrafi aplikacja](#1-co-potrafi-aplikacja)
2. [Jak liczone są pieniądze i limity](#2-jak-liczone-są-pieniądze-i-limity)
3. [Struktura projektu](#3-struktura-projektu)
4. [Development — uruchomienie lokalne](#4-development--uruchomienie-lokalne)
5. [Produkcja — Docker Compose](#5-produkcja--docker-compose)
6. [Domena i HTTPS](#6-domena-i-https)
7. [Hosting współdzielony — cyber_Folks i inne panele DirectAdmin](#7-hosting-współdzielony--cyber_folks-i-inne-panele-directadmin)
8. [Pierwsze uruchomienie i konto administratora](#8-pierwsze-uruchomienie-i-konto-administratora)
9. [Kopie zapasowe](#9-kopie-zapasowe)
10. [Przywracanie danych](#10-przywracanie-danych)
11. [Aktualizacja aplikacji](#11-aktualizacja-aplikacji)
12. [Migracje bazy danych](#12-migracje-bazy-danych)
13. [API i dokumentacja OpenAPI](#13-api-i-dokumentacja-openapi)
14. [Testy](#14-testy)
15. [Bezpieczeństwo](#15-bezpieczeństwo)
16. [Rozbudowa w przyszłości](#16-rozbudowa-w-przyszłości)
17. [Zastrzeżenie](#17-zastrzeżenie)

---

## 1. Co potrafi aplikacja

**Pulpit**
- przychód należny bieżącego kwartału na tle limitu wraz z paskiem wykorzystania,
- progi ostrzeżeń: 75% (ostrzeżenie), 90% (mocne ostrzeżenie), 100% (przekroczenie),
- komunikat o przekroczeniu limitu ze wskazaniem daty, sprzedaży i kwoty ponad limit,
- sprzedaż dzisiaj, przychód należny (miesiąc, kwartał, rok), otrzymane płatności,
  niezapłacone należności, koszty, szacowany dochód, liczba zamówień, średnia wartość
  zamówienia,
- wykresy: 30 dni, sprzedaż miesięczna, przychód należny vs otrzymany, koszty vs
  przychód, sprzedaż wg kanału i wg produktu.

**Sprzedaż i ewidencja**
- sprzedaż z wieloma pozycjami, rabatem, kosztem wysyłki, kanałem, metodą płatności,
  typem klienta (B2C/B2B) i danymi klienta,
- płatności jako osobny model — jedna sprzedaż może mieć wiele wpłat (płatności
  częściowe), zwroty pieniędzy zapisywane są jako płatność ujemna,
- korekty: zwrot całkowity, zwrot częściowy, rabat po sprzedaży, anulowanie, korekta
  wartości, zwrot pieniędzy — z wartością poprzednią, nową, kwotą, powodem i autorem,
- ewidencja sprzedaży z przychodem narastająco oraz uproszczona ewidencja dzienna,
- filtry (zakres dat, dzień, miesiąc, kwartał, rok, produkt, kanał, metoda, status,
  B2B/B2C), sortowanie, wyszukiwanie i paginacja.

**Koszty, produkty, dokumenty**
- koszty z edytowalnymi kategoriami i załącznikami (PDF, JPG, JPEG, PNG, WEBP),
- baza produktów (nazwa, SKU, model, kategoria, cena, koszt produkcji, status),
- rachunki i faktury bez VAT z konfigurowalną numeracją (domyślnie `1/09/2026`),
  danymi sprzedawcy z ustawień i generowaniem PDF po stronie serwera,
- oznaczenia KSeF (poza KSeF / przesłany / numer KSeF) oraz miesięczny licznik
  sprzedaży udokumentowanej fakturami,
- licznik roczny sprzedaży B2C pomocny przy limicie kasy fiskalnej.

**Raporty, PIT, backup**
- raporty: dzienny, miesięczny, kwartalny, roczny, przychód należny, przychód
  otrzymany, koszty, dochód, B2C, B2B, wg produktu, wg kanału, należności
  niezapłacone — eksport CSV, XLSX i PDF (generowane na serwerze),
- podsumowanie PIT (miesięczne, kwartalne, roczne) liczone kasowo,
- kopie zapasowe przez SQLite Backup API, automatyczne kopie o wybranej godzinie,
  retencja, pobieranie, przywracanie z weryfikacją integralności, eksport JSON,
- dziennik zmian (logowania, sprzedaż, korekty, koszty, ustawienia, backupy).

---

## 2. Jak liczone są pieniądze i limity

**Kwoty.** Wszystkie kwoty są liczbami całkowitymi w groszach (`int`), również w API.
Nigdzie nie jest używany typ zmiennoprzecinkowy. Przykład: `10 813,50 zł` to `1081350`.

**Dwa rodzaje przychodu — liczone niezależnie:**

| Pojęcie | Kiedy powstaje | Do czego służy |
|---|---|---|
| Przychód **należny** | w dniu sprzedaży, także gdy klient jeszcze nie zapłacił | kontrola limitu działalności nierejestrowanej |
| Przychód **otrzymany** | w dniu faktycznej wpłaty (model płatności) | dane pomocnicze do PIT |

Data sprzedaży i data otrzymania płatności to osobne pola i osobne wyliczenia.

**Limit kwartalny** jest liczony z parametrów zapisanych w bazie (ekran
*Ustawienia → Rok podatkowy i limity*), a nie zaszytych w kodzie:

```
limit kwartalny = minimalne wynagrodzenie × mnożnik
2026: 4 806,00 zł × 225% = 10 813,50 zł
```

Można też wpisać limit ręcznie — wtedy ma pierwszeństwo nad wyliczonym.
Kwartały: I (I–III), II (IV–VI), III (VII–IX), IV (X–XII); każdy liczony osobno.
Po przekroczeniu limitu aplikacja **ostrzega, ale nie blokuje** dopisywania kolejnych
transakcji.

Konfigurowalne są także progi pomocnicze: KSeF (domyślnie 10 000 zł miesięcznie)
i kasa fiskalna (domyślnie 20 000 zł rocznie).

---

## 3. Struktura projektu

```
backend/                 API (FastAPI + SQLAlchemy + Alembic)
  app/
    api/routes/          endpointy REST
    core/                konfiguracja, bezpieczeństwo, kwoty, daty, błędy
    db/                  silnik SQLite (WAL), sesje, dane startowe
    models/              modele ORM
    repositories/        zapytania i filtry
    schemas/             walidacja wejścia/wyjścia (Pydantic)
    services/            logika biznesowa (limity, sprzedaż, korekty, backup…)
    cli.py               narzędzia administracyjne
  alembic/               migracje bazy
  tests/                 testy backendu (pytest)
frontend/                interfejs (React + TypeScript + Vite)
  src/
    api/                 klient HTTP i endpointy
    components/          komponenty wspólne i wykresy
    features/            formularze sprzedaży, płatności, korekt
    hooks/               sesja, motyw, powiadomienia, słowniki
    pages/               ekrany aplikacji
    types/, utils/       typy i formatowanie (kwoty, daty)
deploy/                  Caddyfile oraz przykładowa konfiguracja Nginx
  cyberfolks/            wdrożenie na hosting współdzielony (Passenger)
    passenger_wsgi.py    plik startowy aplikacji na serwerze
    build-package.sh     buduje dist/ewidencja-hosting.zip do wgrania w panelu
    diagnostyka.py       raport o stanie wdrożenia (uruchamiany z panelu)
    konsola.py           polecenia administracyjne bez SSH
    INSTRUKCJA.txt       skrócona instrukcja dołączana do paczki
data/                    baza SQLite (poza katalogiem publicznym)
backups/                 kopie zapasowe
uploads/                 załączniki dokumentów kosztowych
docker-compose.yml       uruchomienie produkcyjne
.env.example             wzór konfiguracji
```

Katalogi `data/`, `backups/` i `uploads/` nie są wersjonowane i nigdy nie są
serwowane przez serwer WWW — dostęp do nich ma wyłącznie backend.

---

## 4. Development — uruchomienie lokalne

Wymagania: Python 3.11+, Node.js 20+.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

export SECRET_KEY="dowolny-lokalny-klucz"
export APP_ENV=development
python -m app.cli migrate                 # tworzy bazę w ../data/database.sqlite3
python -m app.cli create-admin --login admin   # hasło zostanie zapytane

uvicorn app.main:app --reload --port 8000
```

API: <http://127.0.0.1:8000/api>, dokumentacja: <http://127.0.0.1:8000/api/docs>,
health check: <http://127.0.0.1:8000/health>.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Interfejs: <http://127.0.0.1:5173>. Serwer deweloperski przekazuje `/api` na
`http://127.0.0.1:8000` (zmienisz to zmienną `VITE_API_PROXY`).

---

## 5. Produkcja — Docker Compose

Na serwerze (Linux z Dockerem):

```bash
git clone <adres-repozytorium> ewidencja
cd ewidencja

cp .env.example .env
nano .env                     # domena, SECRET_KEY, dane administratora, APP_UID/APP_GID

mkdir -p data backups uploads
sudo chown -R "$(id -u)":"$(id -g)" data backups uploads

docker compose up -d --build
docker compose ps
docker compose logs -f backend
```

Architektura: `Internet → HTTPS → Caddy (kontener web) → FastAPI (kontener backend) → SQLite`.
Port backendu nie jest publikowany na hoście — jedyną drogą do danych jest proxy.

Minimalna zawartość `.env`:

```env
APP_DOMAIN=ewidencja.mojadomena.pl
ACME_EMAIL=twoj-adres@example.com
SECRET_KEY=<openssl rand -base64 48>
APP_UID=1000
APP_GID=1000
ADMIN_LOGIN=admin
ADMIN_PASSWORD=<mocne-haslo-startowe>
ENABLE_DOCS=0
```

Sekretów nie trzymaj w repozytorium — `.env` jest w `.gitignore`.

Sprawdzenie po starcie:

```bash
curl -fsS https://ewidencja.mojadomena.pl/health
# {"status":"ok","database":"ok","version":"0.1.0"}
```

---

## 6. Domena i HTTPS

### Wariant A — Caddy (domyślny, zalecany)

1. Skieruj rekord `A` (i ewentualnie `AAAA`) domeny na adres IP serwera.
2. Otwórz porty 80 i 443 (`ufw allow 80,443/tcp`).
3. Ustaw `APP_DOMAIN` i `ACME_EMAIL` w `.env`.
4. `docker compose up -d` — Caddy sam pobierze i będzie odnawiał certyfikat
   Let's Encrypt. Konfiguracja: [`deploy/Caddyfile`](deploy/Caddyfile) (montowana do
   kontenera, więc zmiana nie wymaga przebudowy obrazu).

Caddy wysyła nagłówki HSTS, CSP, `X-Content-Type-Options`, `X-Frame-Options`
i `Referrer-Policy`, a całość ruchu przekierowuje na HTTPS.

### Wariant B — Nginx + certbot

Gotowy przykład: [`deploy/nginx.conf`](deploy/nginx.conf).

```bash
sudo apt install nginx certbot python3-certbot-nginx
sudo cp deploy/nginx.conf /etc/nginx/sites-available/ewidencja
sudo ln -s /etc/nginx/sites-available/ewidencja /etc/nginx/sites-enabled/
sudo certbot --nginx -d ewidencja.mojadomena.pl
sudo nginx -t && sudo systemctl reload nginx
```

W tym wariancie backend uruchom lokalnie (np. `127.0.0.1:8000`), a pliki frontendu
zbuduj (`cd frontend && npm ci && npm run build`) i skopiuj do `/var/www/ewidencja`.

---

## 7. Hosting współdzielony — cyber_Folks i inne panele DirectAdmin

Wariant dla zwykłego hostingu WWW, bez Dockera i bez uprawnień administratora
serwera. Aplikację uruchamia **Passenger** z modułu *Aplikacje Python* w panelu
DirectAdmin; ten sam proces serwuje API i interfejs, więc nie trzeba osobnego
serwera plików statycznych. Dostęp SSH jest wygodny, ale niekonieczny — całość
da się przeklikać w panelu.

Czego wymaga hosting:

| Wymaganie | Uwagi |
|---|---|
| moduł *Aplikacje Python* (Passenger) | Python 3.11 lub nowszy |
| instalacja zależności z `requirements.txt` | przycisk w panelu albo SSH |
| zadania cron | do automatycznych kopii zapasowych |
| certyfikat SSL dla domeny | wymagany — ciasteczko sesji ma flagę `Secure` |
| ok. 300 MB miejsca | kod, środowisko Pythona, baza i kopie zapasowe |

### 7.1. Zbuduj paczkę

Paczka zawiera backend, zbudowany interfejs, plik startowy Passengera i wzór
konfiguracji z wygenerowanym `SECRET_KEY` oraz hasłem startowym administratora.

```bash
./deploy/cyberfolks/build-package.sh /ewidencja   # aplikacja pod adresem domena.pl/ewidencja
./deploy/cyberfolks/build-package.sh /            # własna domena lub subdomena
```

Wynik: `dist/ewidencja-hosting.zip`. Skrypt wypisuje na końcu hasło startowe
administratora — zapisz je.

Adres podany przy budowaniu jest wkompilowany w interfejs (ścieżki do plików
i do API). Zmiana adresu na serwerze wymaga zbudowania paczki od nowa.

Bez Node.js na własnym komputerze: zakładka **Actions → Paczka na hosting →
Run workflow** w repozytorium na GitHubie zbuduje ZIP do pobrania
(hasło startowe jest wtedy w pliku `.env.przyklad` wewnątrz paczki).

### 7.2. Utwórz aplikację w panelu

*Panel → Aplikacje Python → Utwórz aplikację*:

| Pole | Wartość |
|---|---|
| wersja Pythona | 3.11 lub nowsza |
| katalog aplikacji (*Application root*) | `ewidencja` — poza `public_html` |
| adres aplikacji (*Application URL*) | `twojadomena.pl/ewidencja` |
| plik startowy (*Application startup file*) | `passenger_wsgi.py` |
| punkt wejścia (*Application Entry point*) | `application` |

Katalog aplikacji **musi leżeć poza `public_html`** — w środku trzymana jest
baza, kopie zapasowe i załączniki. Panel sam utworzy środowisko wirtualne
i katalog aplikacji w domenie.

### 7.3. Wgraj pliki

*Menedżer plików* → katalog aplikacji (np. `/home/UŻYTKOWNIK/ewidencja`):

1. wgraj `ewidencja-hosting.zip`,
2. rozpakuj go w tym katalogu (nadpisując `passenger_wsgi.py` utworzony przez panel),
3. usuń plik ZIP,
4. zmień nazwę `.env.przyklad` na `.env`.

Po rozpakowaniu w katalogu aplikacji są: `passenger_wsgi.py`, `requirements.txt`,
`backend/`, `frontend/`, `data/`, `backups/`, `uploads/`, `.env`.

### 7.4. Sprawdź `.env`

```env
APP_ENV=production
SECRET_KEY=<wygenerowany przez skrypt — nie zmieniaj>
FRONTEND_DIR=frontend
ADMIN_LOGIN=admin
ADMIN_PASSWORD=<hasło startowe>
ENABLE_DOCS=0
COOKIE_SECURE=
```

`COOKIE_SECURE` zostaw puste — w trybie produkcyjnym aplikacja sama włącza flagę
`Secure`, więc domena musi działać po HTTPS.

### 7.5. Zainstaluj zależności i uruchom

*Panel → Aplikacje Python → edycja aplikacji*: wskaż `requirements.txt`, uruchom
instalację zależności (pip), a potem zrestartuj aplikację. Przy pierwszym starcie
aplikacja wykonuje migracje, wgrywa dane słownikowe i zakłada konto administratora
ze zmiennych z `.env`.

Sprawdzenie: `https://twojadomena.pl/ewidencja/health` powinno zwrócić
`{"status":"ok","database":"ok",...}`.

Mając SSH, te same kroki to:

```bash
source /home/UŻYTKOWNIK/virtualenv/ewidencja/3.11/bin/activate
cd /home/UŻYTKOWNIK/ewidencja
pip install -r requirements.txt
cd backend && python -m app.cli migrate
```

### 7.6. Pierwsze logowanie

Zaloguj się na `https://twojadomena.pl/ewidencja`, zmień hasło w *Ustawienia →
Moje konto*, a następnie wyczyść wartość `ADMIN_PASSWORD` w `.env` i zrestartuj
aplikację w panelu.

### 7.7. Automatyczne kopie zapasowe (cron)

Pod Passengerem proces jest usypiany między żądaniami, więc harmonogram kopii
obsługuje cron, a nie pętla w tle. *Panel → Zadania cron*, codziennie o 3:00:

```bash
cd /home/UŻYTKOWNIK/ewidencja/backend && /home/UŻYTKOWNIK/virtualenv/ewidencja/3.11/bin/python -m app.cli auto-backup
```

Dokładną ścieżkę do Pythona pokazuje panel w polu „Wejdź do środowiska
wirtualnego”. Polecenie sprawdza godzinę i ustawienia z aplikacji (*Ustawienia →
Aplikacja*) i tworzy kopię tylko wtedy, gdy jest zaplanowana, więc można je
uruchamiać nawet co godzinę. Kopie na żądanie robisz jak zwykle na ekranie
*Backup*.

Kopie leżą w `backups/` na tym samym dysku co baza — raz w miesiącu pobierz je
na własny komputer (ekran *Backup* → „Pobierz”).

### 7.8. Narzędzia bez SSH — pole „Wykonaj skrypt Python"

Na hostingu bez dostępu SSH rolę wiersza poleceń pełni pole *Wykonaj skrypt
Python* w panelu (*Aplikacje Python*). W paczce są dwa skrypty:

| Polecenie w panelu | Co robi |
|---|---|
| `diagnostyka.py` | sprawdza wersję Pythona, pliki, zależności, reguły `.htaccess` i próbuje uruchomić aplikację; raport zapisuje do `diagnostyka.txt` obok skryptu |
| `konsola.py migrate` | migracje bazy |
| `konsola.py list-users` | lista kont |
| `konsola.py reset-password --login admin --password NoweHaslo123` | nowe hasło użytkownika |
| `konsola.py backup` | kopia zapasowa na żądanie |

`diagnostyka.py` celowo działa także na starszym Pythonie — jeśli aplikacja nie
startuje przez złą wersję interpretera, raport i tak powstanie i to powie.

Hasło podane w polu polecenia zostaje zapisane w konfiguracji aplikacji, więc
po zmianie hasła wyczyść to pole.

### 7.9. Aktualizacja

1. Zrób kopię zapasową (ekran *Backup*).
2. Zbuduj nową paczkę tym samym poleceniem co poprzednio.
3. Wgraj i rozpakuj ją w katalogu aplikacji — nadpisz `backend/`, `frontend/`,
   `passenger_wsgi.py` i `requirements.txt`.
4. **Nie nadpisuj `.env`** — paczka zawiera tylko `.env.przyklad`, więc
   konfiguracja i klucz zostają nietknięte. Nie ruszaj też `data/`, `backups/`
   ani `uploads/`.
5. W panelu zainstaluj zależności ponownie i zrestartuj aplikację — migracje
   wykonają się przy starcie.

### 7.10. Gdy coś nie działa

Pierwszy krok przy każdym z tych objawów: uruchom `diagnostyka.py` (punkt 7.8)
i przeczytaj sekcję „WNIOSEK" w raporcie.

| Objaw | Przyczyna i rozwiązanie |
|---|---|
| błąd 500 zaraz po wgraniu | zajrzyj do `stderr.log` w katalogu aplikacji i do logów domeny w panelu; najczęściej brak zainstalowanych zależności albo brak pliku `.env` |
| „Brak SECRET_KEY…” w logu | plik nadal nazywa się `.env.przyklad` albo leży w złym katalogu (ma być w katalogu aplikacji, obok `passenger_wsgi.py`) |
| pod adresem aplikacji pokazuje się strona WordPressa | reguły WordPressa z `public_html/.htaccess` przepisują na `index.php` wszystko, co nie jest istniejącym plikiem — w tym adresy aplikacji. Dopisz w `public_html/.htaccess`, **nad** blokiem `# BEGIN WordPress` (i nad blokiem LSCACHE): `RewriteEngine On` oraz `RewriteRule ^ewidencja($\|/) - [L]` |
| w `stderr.log` `UnicodeDecodeError: 'ascii' codec` przy starcie | proces ma lokalizację ASCII, a Alembic czyta `alembic.ini` w kodowaniu lokalizacji. Ten plik musi być czystym ASCII — pilnuje tego `tests/test_migracje.py` |
| logowanie od razu wylogowuje | domena działa po HTTP — włącz certyfikat SSL i wymuszenie HTTPS w panelu |
| puste strony, w konsoli błędy 404 na plikach `assets/` | paczka zbudowana dla innego adresu niż rzeczywisty — zbuduj ją ponownie z właściwą ścieżką |
| zmiany w `.env` nic nie dają | po każdej zmianie trzeba zrestartować aplikację w panelu |

### 7.11. Czym ten wariant różni się od Dockera

- HTTPS i domena pochodzą z panelu hostingu, nie z Caddy'ego.
- Automatyczne kopie zapasowe uruchamia cron (punkt 7.7), a nie pętla w tle.
- Pliki statyczne serwuje Python, a nie wyspecjalizowany serwer — przy jednym
  użytkowniku nie ma to znaczenia, ale jest wolniejsze niż wariant z Caddy.
- Baza SQLite i tak trzyma dane w plikach, więc funkcjonalnie nic nie ubywa:
  limity, dokumenty, raporty, PDF-y i kopie zapasowe działają tak samo.

Subdomena (np. `ewidencja.twojadomena.pl`) jest wygodniejsza niż podkatalog —
nie ma wtedy ryzyka konfliktu z regułami `.htaccess` sklepu WordPress. Paczkę
budujesz wtedy poleceniem `./deploy/cyberfolks/build-package.sh /`.

---

## 8. Pierwsze uruchomienie i konto administratora

Administrator powstaje na dwa sposoby.

**Ze zmiennych środowiskowych** (tylko gdy w bazie nie ma jeszcze użytkowników):

```env
ADMIN_LOGIN=admin
ADMIN_PASSWORD=MocneHaslo123
ADMIN_EMAIL=ja@example.com
```

Po pierwszym zalogowaniu zmień hasło (*Ustawienia → Moje konto*) i usuń
`ADMIN_PASSWORD` z `.env`, a następnie `docker compose up -d`.

**Z wiersza poleceń** (zawsze):

```bash
docker compose exec backend python -m app.cli create-admin --login admin
docker compose exec backend python -m app.cli list-users
docker compose exec backend python -m app.cli reset-password --login admin
```

Lokalnie (bez Dockera) te same polecenia uruchamiasz w katalogu `backend/`
z aktywnym środowiskiem wirtualnym.

Wymagania hasła: minimum 10 znaków, małe i wielkie litery oraz cyfra.
Hasła są hashowane algorytmem **Argon2id** — nigdy nie są zapisywane jawnie.

Kolejnych użytkowników dodasz w *Ustawienia → Użytkownicy*. Role: administrator
(pełne uprawnienia), księgowość (bez zmiany ustawień i użytkowników), podgląd
(tylko odczyt). Konto można w każdej chwili dezaktywować.

---

## 9. Kopie zapasowe

Kopie wykonuje **SQLite Backup API** — kopiowanie działającego pliku zwykłym `cp`
grozi uszkodzoną kopią i nie jest tu stosowane.

- **W aplikacji:** ekran *Backup* → „Utwórz kopię zapasową”, „Pobierz”, „Usuń”,
  „Eksport danych (JSON)”.
- **Automatycznie:** domyślnie codziennie o 03:00 (godzina, minuta, włącznik
  i liczba przechowywanych kopii w *Ustawienia → Aplikacja*, domyślnie 30 kopii;
  starsze są usuwane).
- **Z wiersza poleceń:**

```bash
docker compose exec backend python -m app.cli backup
```

- **Z poziomu serwera** (kopia katalogów na inny nośnik):

```bash
tar czf ewidencja-$(date +%F).tar.gz backups uploads .env
```

Nazwy plików: `backup_2026-09-18_21-30-00.sqlite3` (kopie automatyczne mają
dopisek `_auto`). Kopie leżą w katalogu `backups/`.

Zalecenie: przynajmniej raz w miesiącu skopiuj `backups/` i `uploads/` poza serwer.

---

## 10. Przywracanie danych

Ekran *Backup* → „Przywróć” przy wybranej kopii. Aplikacja kolejno:

1. sprawdza integralność pliku (`PRAGMA integrity_check` i obecność tabel aplikacji),
2. wykonuje automatyczną kopię bezpieczeństwa aktualnej bazy,
3. wymaga zaznaczenia zgody i wpisania słowa `PRZYWRACAM`,
4. dopiero wtedy podmienia bazę i uruchamia migracje do bieżącej wersji.

Po przywróceniu trzeba zalogować się ponownie (sesje pochodzą z przywróconej bazy).

Ręczne przywrócenie na serwerze:

```bash
docker compose stop backend
cp backups/backup_2026-09-18_21-30-00.sqlite3 data/database.sqlite3
rm -f data/database.sqlite3-wal data/database.sqlite3-shm
docker compose start backend
```

---

## 11. Aktualizacja aplikacji

Wariant z Dockerem. Dla hostingu współdzielonego aktualizację opisuje punkt 7.9.

```bash
cd ewidencja
docker compose exec backend python -m app.cli backup     # kopia przed aktualizacją
git pull
docker compose build
docker compose up -d
docker compose logs -f backend                            # migracje w logu startu
curl -fsS https://ewidencja.mojadomena.pl/health
```

Aktualizacja nie usuwa bazy, kopii zapasowych ani załączników — te dane leżą
w katalogach hosta (`data/`, `backups/`, `uploads/`) montowanych do kontenera.
Migracje wykonują się automatycznie przy starcie kontenera i nie kasują danych.

Wycofanie zmiany: `git checkout <poprzedni-tag>` i ponowny `docker compose up -d --build`,
w razie potrzeby wraz z przywróceniem kopii (punkt 10).

---

## 12. Migracje bazy danych

Migracjami zarządza **Alembic** (`backend/alembic/`).

```bash
# w kontenerze
docker compose exec backend python -m app.cli migrate
docker compose exec backend alembic current
docker compose exec backend alembic history

# lokalnie (backend/, aktywne .venv)
alembic upgrade head
alembic revision --autogenerate -m "opis zmiany"
alembic downgrade -1
```

Każda zmiana schematu wymaga migracji. Warstwa danych nie korzysta z funkcji
specyficznych dla SQLite, więc przejście na PostgreSQL sprowadza się do zmiany
`DATABASE_URL` (moduł kopii zapasowych pozostaje wtedy do wymiany — SQLite Backup
API dotyczy wyłącznie SQLite).

---

## 13. API i dokumentacja OpenAPI

Wszystkie ścieżki są pod prefiksem `/api`:

| Zasób | Ścieżka |
|---|---|
| logowanie, sesja, hasło | `/api/auth` |
| użytkownicy | `/api/users` |
| sprzedaż | `/api/sales` |
| płatności | `/api/sales/{id}/payments`, `/api/payments/{id}` |
| korekty | `/api/sales/{id}/corrections` |
| ewidencja | `/api/registry`, `/api/registry/daily` |
| koszty i kategorie | `/api/costs`, `/api/cost-categories` |
| załączniki | `/api/attachments` |
| produkty | `/api/products` |
| dokumenty | `/api/documents` |
| raporty i eksporty | `/api/reports` |
| pulpit, limity, PIT | `/api/dashboard`, `/api/limits`, `/api/pit` |
| ustawienia i rok podatkowy | `/api/settings`, `/api/settings/fiscal-years` |
| kopie zapasowe | `/api/backups` |
| dziennik zmian | `/api/audit-logs` |
| health check | `/health` (bez logowania) |

Swagger i OpenAPI (`/api/docs`, `/api/redoc`, `/api/openapi.json`) są włączane
zmienną `ENABLE_DOCS`. W produkcji domyślnie wyłączone (`ENABLE_DOCS=0`).

---

## 14. Testy

```bash
# backend
cd backend && source .venv/bin/activate
pytest                      # 67 testów

# frontend
cd frontend
npm test                    # 17 testów (vitest)
npm run typecheck
npm run build
```

Testy backendu obejmują m.in. logowanie i limit prób, uprawnienia ról, CSRF,
przypisanie sprzedaży do kwartału, limit kwartalny i wykrycie przekroczenia
(z datą, sprzedażą i kwotą ponad limit), przychód należny i otrzymany, płatności
częściowe, zwroty, rabaty, anulowanie, korekty wartości, koszty, załączniki,
raporty i eksporty, numerację dokumentów, PDF, backup oraz przywracanie bazy.

---

## 15. Bezpieczeństwo

- logowanie wymagane do każdego zasobu poza `/health`,
- sesje serwerowe; w ciasteczku `HttpOnly` (`Secure` i `SameSite` w produkcji)
  znajduje się token, w bazie wyłącznie jego skrót SHA-256,
- w `localStorage` nie ma żadnych tokenów (tylko wybór motywu),
- ochrona CSRF: token sesji wysyłany nagłówkiem `X-CSRF-Token` i weryfikowany
  przy każdej operacji zapisu,
- limit prób logowania (domyślnie 5 w 15 minut) i czasowa blokada konta,
- hasła: Argon2id; możliwość dezaktywacji użytkownika,
- walidacja całego wejścia po stronie backendu (Pydantic) niezależnie od frontendu,
- zapytania przez SQLAlchemy (parametryzowane — brak ryzyka SQL Injection),
- nagłówki bezpieczeństwa z aplikacji i z reverse proxy (HSTS, CSP, nosniff,
  DENY dla ramek),
- uploady: kontrola rozszerzenia, typu MIME i sygnatury pliku, limit rozmiaru
  (konfigurowalny), losowa nazwa na dysku, katalog poza serwerem WWW, pobieranie
  tylko po zalogowaniu,
- błędy serwera trafiają do logu; użytkownik widzi komunikat bez szczegółów,
- dziennik zmian nie zapisuje haseł ani tokenów,
- dane finansowe kasowane są miękko (`deleted_at`) — historia zostaje.

---

## 16. Rozbudowa w przyszłości

Projekt jest przygotowany pod dalszy rozwój:

- warstwy `services/` i `repositories/` oddzielają logikę od API — dodanie
  integracji (WooCommerce, Allegro, automatyczne pobieranie zamówień) sprowadza się
  do nowego serwisu i endpointu,
- model sprzedaży ma pozycje, kanał sprzedaży i dane klienta, więc import zamówień
  z zewnętrznego sklepu nie wymaga zmiany schematu,
- produkty mają pole `attributes` (JSON) na przyszłe dane: numer partii, numer
  seryjny, wersja produktu, dokumentacja GPSR, instrukcje, informacje bezpieczeństwa,
- dokumenty mają pola KSeF (status i numer) — brakuje wyłącznie integracji z API KSeF,
- role użytkowników i audyt działają od początku, więc wielu użytkowników nie wymaga
  przebudowy,
- wartości prawne i podatkowe (limity, progi, mnożniki, numeracja) są w bazie,
  więc zmiana przepisów to zmiana ustawień, a nie kodu.

---

## 17. Zastrzeżenie

Aplikacja jest narzędziem pomocniczym do prowadzenia własnej ewidencji. Nie jest
certyfikowanym systemem księgowym, nie składa deklaracji podatkowych i nie zastępuje
porady podatkowej ani oficjalnych systemów rozliczeń. Limity i progi przyjęte
domyślnie należy zweryfikować z aktualnymi przepisami — wszystkie są edytowalne
w ustawieniach.
