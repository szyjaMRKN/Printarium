---
name: verify-links
description: >
  Weryfikacja linków WWW zanim trafią do użytkownika — sprawdzenie, czy strona
  faktycznie istnieje i mówi o tym, o czym twierdzisz, oraz dobór form linków
  odpornych na wygasanie. Użyj ZAWSZE, gdy odpowiedź ma zawierać adresy URL:
  źródła, „podaj linki", linki do produktów/sklepów/ofert, dokumentacji, datasheetów,
  artykułów, repozytoriów, a także gdy wpisujesz linki do pliku (README, dokumentacja,
  raport, notatka). Dotyczy też sytuacji, gdy linki pochodzą z wyszukiwarki —
  wynik wyszukiwania to kandydat, nie potwierdzenie. Także po angielsku:
  "find links", "sources", "cite", "where can I buy".
---

# Weryfikacja linków przed podaniem ich użytkownikowi

Link z indeksu wyszukiwarki to **kandydat, nie potwierdzenie**. Indeksy bywają
nieaktualne o miesiące: oferta wygasła, sklep przebudował adresy, strona jest
geoblokowana. Podanie takiego linku jako źródła jest gorsze niż niepodanie
żadnego — użytkownik traci czas na klikanie w martwe adresy i przestaje ufać
reszcie odpowiedzi.

## Ścieżka podstawowa

1. **Zbierz kandydatów** — wyszukiwarką (WebSearch) albo z dokumentacji.
2. **Pobierz każdy kandydat** (WebFetch, równolegle w jednym bloku wywołań)
   i zapytaj o coś, co potwierdzi treść: nazwę produktu, model, dostępność,
   tytuł artykułu. Sam kod 200 nie wystarcza — sklepy zwracają 200 dla stron
   „produkt niedostępny", a wyszukiwarki dla stron błędu.
3. **Zakwalifikuj wynik** wg tabeli niżej.
4. **Podaj tylko to, co potwierdzone**, a resztę oznacz jawnie.

## Jak czytać niepowodzenie

Rozróżnienie jest kluczowe, bo prowadzi do zupełnie innych działań:

| Objaw | Co to znaczy | Co zrobić |
|---|---|---|
| Treść zgadza się z tym, co twierdzisz | link działa | podaj |
| 404, 410, „nie znaleziono", strona pusta | link martwy | odrzuć, szukaj innego |
| 200, ale treść o czymś innym / oferta zakończona | link mylący | odrzuć |
| `EGRESS_BLOCKED`, proxy odpowiada 403 na CONNECT, `curl: (56)` | **ograniczenie Twojego środowiska**, nie dowód, że strona nie działa | nie twierdź nic o stanie strony — patrz „Gdy weryfikacja jest niemożliwa" |
| 403 od samego serwisu (ochrona przed botami, np. Cloudflare) | stan nieznany | traktuj jak niezweryfikowany |

Zanim uznasz stronę za martwą, upewnij się, że to nie blokada środowiska.
W Claude Code na zdalnym środowisku sprawdzisz to jednym poleceniem:

```bash
curl -sS "$HTTPS_PROXY/__agentproxy/status" | head -40   # sekcja recentRelayFailures
```

Jeśli widnieje tam `connect_rejected` / „policy denial" dla Twojej domeny —
problem jest po stronie proxy. Nie obchodź tego (`-k`, zdejmowanie `HTTPS_PROXY`);
po prostu zgłoś ograniczenie.

## Gdy weryfikacja jest niemożliwa

Zdarza się, że wyszukiwarka działa (jest po stronie serwera), a pobieranie stron
jest odcięte. Wtedy:

1. **Powiedz to jednym zdaniem**, bez rozwlekłych tłumaczeń:
   „Nie mogłem otworzyć tych stron z tego środowiska (sieć zablokowana), więc
   linki są niezweryfikowane."
2. **Przenieś ciężar informacji z linku na treść.** Numer katalogowy, model,
   parametry, ISBN, DOI, nazwa pakietu i wersja przeżyją każdą przebudowę sklepu.
   Link jest wygodą, identyfikator jest trwałą informacją.
3. **Wybierz trwalsze formy adresów** (kolejność od najtrwalszej):
   - strona producenta / oficjalna dokumentacja / rejestr (DOI, PyPI, npm),
   - adres wyszukiwania w serwisie, np. `allegro.pl/listing?string=ksd9700`
     — koduje zapytanie, nie identyfikator oferty, więc działa także za rok,
   - kategoria lub listing,
   - **na końcu** głęboki link do pojedynczej oferty z numerem w adresie —
     te wygasają najszybciej.

## Czego nie robić

- **Nie konstruuj adresów z domysłu.** Podmiana `/us/en-us/` na `/pl/`,
  zgadywanie `/szukaj?s=…` czy dopisywanie ID produktu daje adresy, które
  wyglądają wiarygodnie i prowadzą donikąd. Używaj wyłącznie adresów, które
  wróciły z wyszukiwarki albo które udało się pobrać.
- **Nie podawaj linku „na wszelki wypadek"**, żeby lista źródeł wyglądała bogato.
  Trzy działające linki są warte więcej niż osiem, z których połowa jest martwa.
- **Nie zapewniaj, że sprawdziłeś**, jeśli tylko widziałeś adres w wynikach
  wyszukiwania. To najczęstszy sposób, w jaki ta sprawa idzie źle.

## Jak to raportować

Krótko, bez tabelek ze statusami, jeśli wszystko działa. Gdy część linków jest
niepewna, oznacz właśnie te:

```
- [KSD9700 45 °C NC — Elstat](https://…) — sprawdzone, produkt dostępny
- [Datasheet DS18B20](https://…) — ⚠ nie udało się otworzyć z tego środowiska
```

Gdy piszesz linki **do pliku** (README, dokumentacja, raport), przyjmij ostrzejsze
kryterium niż w rozmowie: plik przeżyje sesję i nikt go później nie sprawdzi.
Do plików wpisuj linki trwałe (producent, dokumentacja, adres wyszukiwania)
i zawsze obok nich numer katalogowy albo dokładną nazwę modelu.

## Przykład

**Źle:** „Oto linki do termostatu: [oferta Allegro nr 7338456356], [sklep XYZ]"
— oba z wyników wyszukiwarki, żadnego nie otwarto, oferta z 2013 roku.

**Dobrze:** „Szukaj: **KSD9700, wersja NC, 45 °C, 5 A/250 V** (ok. 5 zł).
[Listing na Allegro](https://allegro.pl/listing?string=ksd9700) — sprawdź opis,
sprzedawcy mylą NC z NO. Stron sklepów nie udało mi się otworzyć z tego
środowiska, więc ceny i dostępność potwierdź sam."
