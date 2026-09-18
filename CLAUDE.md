# Printarium — motyw WooCommerce

Motyw WordPress/WooCommerce dla sklepu z formikariami, terrariami i akcesoriami
dla hodowców bezkręgowców. Ciemna kolorystyka, zielony akcent, Montserrat.

Cała komunikacja z użytkownikiem i wszystkie treści motywu są **po polsku**.

## Układ repozytorium

```
printarium/          źródła motywu (to jest cały deliverable)
build.sh             buduje dist/printarium.zip do wgrania w WordPressie
README.md            instrukcja instalacji i konfiguracji dla użytkownika
dist/                wynik builda (w .gitignore)
```

Branch roboczy: `claude/woocommerce-shop-template-cid120`.

## Komendy

```bash
./build.sh            # lint PHP + spakowanie → dist/printarium.zip
./build.sh 1.1.0      # dodatkowo podbija wersję w style.css i functions.php
```

`build.sh` sam przerywa build, jeśli `php -l` wykryje błąd składni.

## Architektura motywu

Klasyczny motyw PHP (nie block theme). `functions.php` tylko ładuje pliki z `inc/`
— kolejność ma znaczenie, bo `inc/woocommerce.php` wywołuje funkcje z
`inc/template-tags.php` już na etapie wczytywania pliku.

| Plik | Odpowiada za |
|---|---|
| `inc/setup.php` | wsparcie funkcji WP, menu, obszary widgetów, rozmiary obrazków |
| `inc/enqueue.php` | ładowanie CSS/JS |
| `inc/icons.php` | zestaw ikon SVG (`printarium_icon()`) |
| `inc/template-tags.php` | funkcje pomocnicze szablonów, breadcrumbs, paginacja |
| `inc/customizer.php` | opcje w Personalizatorze + `printarium_option()` |
| `inc/shortcodes.php` | `[printarium_faq]`, `[printarium_categories]`, `[printarium_contact_form]` |
| `inc/woocommerce.php` | cała integracja sklepu, przebudowa karty produktu |
| `inc/demo-content.php` | importer danych przykładowych |
| `inc/admin-page.php` | panel „Wygląd → Printarium” |

Arkusze stylów ładowane w tej kolejności: `main.css` → `woocommerce.css` → `wc-blocks.css`.

## System projektowy

**Źródłem prawdy są tokeny w bloku `:root` w `assets/css/main.css`.** Nie wpisuj
wartości kolorów ani rozmiarów na sztywno w komponentach — sięgaj po `var(--pr-*)`.

Kolory bazowe: `#07110D` tło, `#0D1913` powierzchnia, `#829B2F` zieleń,
`#F3F4EF` tekst, `#9CA59E` pomocniczy, `#D65C5C` błąd, `#6BAB6B` sukces.

Typografia: Montserrat w wagach 400/500/600/700. H1 40→64 px/700/wersaliki,
H2 26→32 px/600, body 16 px/400, label 14 px/500, caption 12 px/400,
cena 24→28 px/600. Nagłówki i cena skalują się przez `clamp()`.

Siatka 8 px, promienie 8 px i 12 px.

Uwaga: przezroczystości (`rgba()`) są wyprowadzone z palety ręcznie i **nie
przebudują się** automatycznie po zmianie koloru bazowego w `:root`.

## Konwencje kodu

- Standard WordPress Coding Standards, wcięcia tabulatorami.
- Prefiks `printarium_` dla wszystkich funkcji, `--pr-` dla tokenów CSS,
  `pr-` dla klas komponentów systemu projektowego, BEM dla reszty.
- Text domain `printarium`, wszystkie ciągi przez `__()` / `esc_html__()`.
- Escapowanie na wyjściu zawsze; przy `printarium_get_icon()` dopisz
  `// phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped`.
- JS bez zależności zewnętrznych (vanilla), IIFE, `assets/js/main.js`.

## Pułapki WooCommerce (potwierdzone w tym projekcie)

Te błędy już raz wystąpiły i zostały naprawione — nie cofaj tych rozwiązań.

1. **Clearfixy `::before`/`::after` w kontenerze grid.** WooCommerce dodaje je do
   `ul.products`, `div.product` i kontenerów koszyka. W gridzie stają się pustymi
   komórkami i przesuwają pierwszy produkt o kolumnę. Rozwiązanie: `content: none`
   na tych pseudoelementach (blok na początku sekcji 12 w `main.css`).

2. **`woocommerce-layout.css` wygrywa specyficznością** na `div.images` i
   `div.summary` (`float` + `width: 48%`). Motyw układa je w gridzie, więc te
   właściwości nadpisane są przez `!important` — to konieczne, nie zaniedbanie.

3. **Koszyk i zamówienie to bloki, nie klasyczne szablony.** Nowe instalacje
   WooCommerce używają `wc-block-*`. Klasyczne style z `woocommerce.css` ich nie
   dotyczą — ciemną stylistykę dla nich trzyma osobny `assets/css/wc-blocks.css`.
   Pola formularzy bloków wymagają `!important`, bo mają wysoką specyficzność.

4. **Karta produktu jest przebudowana od zera.** W `inc/woocommerce.php` usunięte
   są `woocommerce_template_loop_product_link_open/close` i
   `woocommerce_template_loop_product_thumbnail`. Bez tego zdjęcie renderuje się
   dwa razy, a przycisk trafia wewnątrz znacznika `<a>`.

5. **`page.php` używa `has_excerpt()`, nie `get_the_excerpt()`.** WordPress
   generuje zajawkę automatycznie z treści, więc podtytuł powielał całą stronę.

## Weryfikacja zmian

Kontener sesji jest efemeryczny — lokalna instalacja WordPressa nie przetrwa do
następnego czatu i trzeba ją odtworzyć. Sprawdzony przepis (wszystko w katalogu
scratchpad, nie w repo):

1. WordPress z `wordpress.org/latest.tar.gz` + `wp-cli.phar`.
2. Baza: wtyczka `sqlite-database-integration`, jej `db.copy` skopiowany do
   `wp-content/db.php` (podstaw pustą wartość za placeholder ścieżki — plik ma
   fallback na `realpath(__DIR__ . '/plugins/sqlite-database-integration')`).
3. `wp core install`, `wp plugin install woocommerce --activate`,
   `wp theme activate printarium`.
4. Dane: `wp eval 'printarium_run_demo_import();'`.
5. Polskie ciągi: `wp language core install pl_PL --activate` oraz
   `wp language plugin install woocommerce pl_PL`.
6. Serwer `php -S localhost:8099`, zrzuty przez Playwright
   (`/opt/node22/lib/node_modules/playwright`, Chromium z `/opt/pw-browsers/chromium`).

Uwaga: strony WooCommerce mają wtedy angielskie slugi (`/shop/`, `/cart/`,
`/checkout/`, `/product/...`), bo powstają przy instalacji wtyczki.
Błędy Action Scheduler w logu to ograniczenie SQLite, nie motywu.

Przy zmianach wizualnych **sprawdzaj realny render**, a nie tylko składnię CSS —
wszystkie pułapki wyżej wyszły dopiero na zrzutach ekranu.

## Czego nie robić

- Nie twórz `woocommerce.php` w katalogu głównym motywu — przejmie wszystkie
  szablony wtyczki i wyłączy nadpisania z `printarium/woocommerce/`.
- Nie wpisuj numerów wersji ani nazw modeli w commity, kod i README.
- Regulamin i polityka prywatności w importerze to celowo tylko szkielet —
  nie udawaj, że są gotowymi dokumentami prawnymi.

---

# Ewidencja działalności nierejestrowanej — druga aplikacja w repozytorium

Na branchu `claude/unregistered-activity-app-uxg6hw` obok motywu żyje samodzielna
aplikacja webowa (`backend/` + `frontend/`) do prowadzenia ewidencji polskiej
działalności nierejestrowanej. Pełna dokumentacja: `README.md`.
Dokumentacja motywu WooCommerce została przeniesiona do `docs-motyw-printarium.md`.

## Układ

```
backend/     FastAPI + SQLAlchemy + Alembic + SQLite (services/, repositories/, api/)
frontend/    React + TypeScript + Vite (pages/, features/, components/, api/)
deploy/      Caddyfile i przykładowa konfiguracja Nginx
data/ backups/ uploads/    dane środowiska (w .gitignore)
```

## Komendy

```bash
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
cd backend && .venv/bin/python -m pytest          # testy backendu
cd backend && .venv/bin/python -m app.cli migrate # migracje + dane startowe
cd frontend && npm install && npm test && npm run build
docker compose config                              # walidacja wdrożenia
./deploy/cyberfolks/build-package.sh /ewidencja    # paczka na hosting współdzielony
```

## Zasady, których nie wolno cofać

1. **Kwoty tylko jako `int` w groszach** — nigdy float, także w API i schematach.
2. **Limity, progi i mnożniki żyją w bazie** (`fiscal_years`, `settings`), nie w kodzie
   liczącym. Limit kwartalny = minimalne wynagrodzenie × mnożnik (2026: 4806 zł × 225%).
3. **Przychód należny ≠ przychód otrzymany.** Pierwszy liczy się od daty sprzedaży
   (limit), drugi od daty wpłaty (PIT). Osobne pola, osobne zapytania.
4. **Płatności to osobny model** — obsługa wpłat częściowych; zwrot pieniędzy to
   płatność ujemna powiązana z korektą.
5. **Nie usuwamy danych finansowych fizycznie** — soft delete (`deleted_at`) i korekty
   z historią (wartość poprzednia, nowa, powód, użytkownik).
6. **Kopie zapasowe wyłącznie przez SQLite Backup API** (`sqlite3.Connection.backup`),
   nigdy `cp` na aktywnym pliku bazy. Przywracanie: weryfikacja → kopia bezpieczeństwa
   → potwierdzenie → podmiana → migracje.
7. **Przeliczenia sprzedaży tylko w `sales_service.recalculate`** — to jedyne miejsce
   ustawiające `accrued_revenue_gr`, `paid_amount_gr` i `payment_status`.
8. **Brak funkcji specyficznych dla SQLite w logice** (grupowanie po datach robimy
   w Pythonie), żeby dało się przejść na PostgreSQL.
9. **Sesja w ciasteczku HttpOnly + token CSRF w nagłówku**; żadnych tokenów
   w `localStorage`.
10. **Puste wpisy w `.env`** (np. `COOKIE_SECURE=`) muszą być traktowane jak brak
    wartości — obsługuje to walidator w `app/core/config.py`.
11. **Dwie drogi wdrożenia, jedna aplikacja.** Docker Compose (Caddy serwuje pliki
    statyczne) oraz hosting współdzielony z Passengerem (`deploy/cyberfolks/`),
    gdzie ten sam proces oddaje API i powłokę SPA — włącza to `FRONTEND_DIR`.
    Pod Passengerem nie działa `lifespan`, więc migracje odpala `passenger_wsgi.py`,
    a harmonogram kopii — cron wywołujący `python -m app.cli auto-backup`.
12. **Adres aplikacji w domenie jest wkompilowany w build frontendu**
    (`VITE_BASE_PATH` → `import.meta.env.BASE_URL`): ścieżki API, `basename`
    routera i zasięg service workera liczą się od niego. Nie wpisuj `/api`
    ani `/sw.js` na sztywno.
