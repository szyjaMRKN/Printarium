# Printarium — motyw WooCommerce

Ciemny motyw WordPress/WooCommerce zbudowany na podstawie layoutu strony głównej
oraz systemu projektowego Printarium (UI Design System 01–03).

Repozytorium zawiera źródła motywu (`printarium/`) oraz skrypt budujący paczkę ZIP
gotową do wgrania w panelu WordPressa.

Poza motywem znajduje się tu również osobny projekt sprzętowy:
[`terrarium-thermostat/`](terrarium-thermostat/README.md) — termostat terrarium
na module Seeed XIAO ESP32-C3 (czujnik DS18B20, przekaźnik maty grzewczej,
sterowanie przez przeglądarkę).

---

## 1. Instalacja

### Wariant A — gotowa paczka ZIP

1. Zbuduj paczkę: `./build.sh` (powstanie plik `dist/printarium.zip`).
2. W panelu WordPress: **Wygląd → Motywy → Dodaj nowy → Wyślij motyw na serwer**.
3. Wskaż `printarium.zip` i kliknij **Zainstaluj**, a następnie **Włącz**.

### Wariant B — wgranie przez FTP

Skopiuj katalog `printarium/` do `wp-content/themes/` i włącz motyw w panelu.

### Wymagania

| Element | Wersja |
|---|---|
| WordPress | 6.0 lub nowszy |
| PHP | 7.4 lub nowszy |
| WooCommerce | 7.0 lub nowszy (opcjonalne, ale wymagane dla funkcji sklepu) |

---

## 2. Konfiguracja w 3 krokach

1. Zainstaluj i włącz wtyczkę **WooCommerce** (przejdź jej kreator: waluta PLN, kraj Polska).
2. Wejdź w **Wygląd → Printarium** i kliknij **Uruchom import**.
3. Wgraj logo i zdjęcie hero w **Wygląd → Dostosuj → Printarium**.

Import tworzy:

- **kategorie sklepu**: Terraria, Terraria plus, Formikaria i areny, Zwierzęta, Akcesoria;
- **25 przykładowych produktów** z cenami, stanami magazynowymi, opisami, atrybutami
  i wygenerowanymi zdjęciami zastępczymi w kolorystyce motywu;
- **atrybuty globalne**: kolor, materiał, rozmiar;
- **podstrony**: Strona główna, Oferta, Kontakt, O nas, FAQ, Dostawa i płatności,
  Zwroty i reklamacje, Regulamin, Polityka prywatności — wypełnione tekstem przykładowym;
- **menu**: główne (kategorie + Oferta + Kontakt), stopki oraz prawne — od razu przypisane
  do lokalizacji motywu;
- **ustawienia**: statyczna strona główna, waluta PLN, format ceny `249,00 zł`, ładne odnośniki.

Import można uruchamiać wielokrotnie — istniejące wpisy są pomijane, nie nadpisywane.
Wszystko, co zostało utworzone, da się usunąć przyciskiem **Usuń dane demonstracyjne**
(usuwa wyłącznie elementy oznaczone przez importer, nie rusza Twoich własnych treści).

---

## 3. Co jest w motywie

### Strona główna

Sekcje odwzorowujące layout: hero z nagłówkiem i dwoma przyciskami, kafle kategorii
z heksagonalną strzałką, pasek czterech atutów, sekcja „Stworzone dla Twojego świata”
z dużymi kaflami, siatka polecanych produktów i akordeon FAQ.

### Sklep

- karta produktu z plakietką (Nowość / Promocja / Brak w magazynie), oceną, ceną
  z przekreśloną ceną regularną, statusem dostępności, chipsami atrybutów i przyciskiem
  „Dodaj do koszyka”;
- pasek narzędzi nad listą: licznik wyników, sortowanie, przełącznik siatka/lista;
- boczny panel filtrów (na mobile wysuwany), stan pusty „Nie znaleziono produktów”;
- wysuwany mini-koszyk z licznikiem odświeżanym przez AJAX;
- karta produktu, koszyk, zamówienie i moje konto w stylistyce systemu projektowego.

### Komponenty systemu projektowego

Przyciski (primary / secondary / ghost / icon we wszystkich stanach), pola formularzy
ze stanami focus/filled/error/disabled, checkboxy, radio, toggle, chipsy, stepper ilości,
badge, tooltipy, komunikaty, toasty, modal, spinner, pasek postępu, skeleton, akordeon.

### Shortcode'y

| Shortcode | Działanie |
|---|---|
| `[printarium_faq]` | Akordeon z pytaniami (`single="false"` pozwala otwierać wiele naraz) |
| `[printarium_categories limit="5"]` | Kafle kategorii sklepu |
| `[printarium_contact_form title="…" to="…"]` | Formularz zapytania z uploadem pliku |

Treść FAQ podmienisz filtrem `printarium_faq_items` w pliku motywu potomnego.

---

## 4. Personalizacja

**Wygląd → Dostosuj → Printarium** zawiera: teksty i przyciski hero, zdjęcie hero,
cztery atuty, tytuł sekcji produktowej, opis i dane kontaktowe w stopce, tekst praw
autorskich oraz przełącznik ładowania fontu Montserrat z Google Fonts (wyłącz, jeśli
hostujesz font lokalnie ze względu na RODO).

Kolory i typografia pochodzą z tokenów CSS w `assets/css/main.css`:

```css
--pr-bg: #07110D;      /* Tło */
--pr-surface: #0D1913; /* Powierzchnia */
--pr-green: #829B2F;   /* Zieleń */
--pr-text: #F3F4EF;    /* Tekst */
--pr-muted: #9CA59E;   /* Pomocniczy */
--pr-error: #D65C5C;   /* Błąd */
--pr-success: #6BAB6B; /* Sukces */
```

Zmiana wartości w bloku `:root` przebudowuje cały motyw.

### Obszary widgetów

- **Sidebar sklepu** — miejsce na filtry (filtr ceny, kategorie, atrybuty, oceny).
  Puste = sklep wyświetla się na pełnej szerokości.
- **Stopka – kolumna 1/2/3** — nadpisują domyślną zawartość kolumn stopki.

---

## 5. Struktura katalogów

```
printarium/
├── assets/
│   ├── css/     main.css (design system), woocommerce.css, admin.css, editor.css
│   ├── js/      main.js (menu, mini-koszyk, akordeon, toasty, stepper, filtry)
│   └── images/  placeholder.svg
├── inc/
│   ├── setup.php          wsparcie funkcji, menu, obszary widgetów
│   ├── enqueue.php        ładowanie zasobów
│   ├── icons.php          zestaw ikon SVG
│   ├── template-tags.php  funkcje pomocnicze szablonów
│   ├── customizer.php     opcje w Personalizatorze
│   ├── shortcodes.php     FAQ, kategorie, formularz kontaktowy
│   ├── woocommerce.php    integracja i układ sklepu
│   ├── demo-content.php   importer danych przykładowych
│   └── admin-page.php     panel Wygląd → Printarium
├── template-parts/
│   ├── home/    hero, categories, usp, highlights, products, faq
│   └── …        mobile-menu, content-card, content-none
├── woocommerce/ nadpisania szablonów (pusty koszyk, brak produktów)
├── functions.php, header.php, footer.php, front-page.php, page.php, single.php,
│   index.php, archive.php, search.php, searchform.php, 404.php, sidebar.php
├── theme.json, style.css, screenshot.png
```

---

## 6. Budowanie paczki

```bash
./build.sh              # → dist/printarium.zip
./build.sh 1.1.0        # dodatkowo podbija numer wersji w style.css
```

Skrypt pomija pliki deweloperskie (`.git`, `.DS_Store`, `node_modules`) i weryfikuje
składnię PHP przed spakowaniem.

---

## 7. Uwagi

- Regulamin i polityka prywatności zawierają **wyłącznie szkielet** — przed
  uruchomieniem sklepu zastąp je dokumentami przygotowanymi prawnie.
- Zdjęcia produktów generowane przez importer to grafiki zastępcze. Podmienisz je
  w edytorze produktu (**Zdjęcie produktu**) oraz kategorii (**Produkty → Kategorie → Miniatura**).
- Ulubione produkty zapisywane są lokalnie w przeglądarce (`localStorage`).
  Pełna lista życzeń po stronie konta wymaga osobnej wtyczki.
