# Termostat terrarium — XIAO ESP32-C3

Prosty termostat do terrarium: czujnik **DS18B20** mierzy temperaturę, **przekaźnik**
załącza matę grzewczą, a podgląd i nastawy odbywają się przez przeglądarkę.

Zgodnie z założeniem po dogrzaniu do temperatury zadanej moduł robi **przerwę
(domyślnie 5 minut), w trakcie której nie wykonuje żadnego pomiaru** — ciepło ma
czas rozejść się po terrarium, a przekaźnik nie „klika” co kilkanaście sekund.

---

## 1. Potrzebne części

| Element | Uwagi |
|---|---|
| Seeed Studio XIAO ESP32-C3 | zasilany z USB-C (5 V) |
| Czujnik DS18B20 | najlepiej wersja wodoodporna, na przewodzie |
| Rezystor 4,7 kΩ | podciągający linię danych czujnika (obowiązkowy) |
| Moduł przekaźnika 1-kanałowy | z optoizolacją, sterowany 3,3 V, styk min. 10 A / 250 V |
| Mata grzewcza | zasilanie zgodne z jej instrukcją |
| Termostat bimetaliczny + bezpiecznik termiczny | zabezpieczenie sprzętowe — patrz [sekcja 3](#3-termostat-bezpieczeństwa-mocno-zalecany) |

Sterowanie przekaźnikiem musi działać z 3,3 V — część tanich modułów wymaga 5 V na
wejściu IN i przy 3,3 V nie przełącza się pewnie. Moduł przekaźnika można zasilić
z pinu 5V modułu XIAO (gdy płytka jest podłączona do USB), ale **masa musi być wspólna**.

---

## 2. Połączenia

### DS18B20

| DS18B20 | XIAO ESP32-C3 |
|---|---|
| GND (czarny) | GND |
| VDD (czerwony) | 3V3 |
| DQ (żółty) | **D1 (GPIO3)** |

Między **DQ a 3V3** wlutuj rezystor **4,7 kΩ**. Czujnik zasilamy normalnie (trzy żyły) —
tryb pasożytniczy nie jest wspierany przez ten program.

### Przekaźnik

| Moduł przekaźnika | XIAO ESP32-C3 |
|---|---|
| VCC | 5V (lub 3V3, jeśli moduł tego wymaga) |
| GND | GND |
| IN | **D2 (GPIO4)** |

Mata grzewcza wpinana jest w styk **NO (normalnie otwarty)** przekaźnika — przy braku
zasilania modułu grzanie jest wyłączone.

```
        ┌─────────────────────┐
        │  XIAO ESP32-C3      │
   USB ─┤ 5V  3V3  GND        │
        │                     │
        │  D1 (GPIO3) ────────┼──── DQ  DS18B20  (+ 4,7 kΩ do 3V3)
        │  D2 (GPIO4) ────────┼──── IN  moduł przekaźnika ──► mata grzewcza
        └─────────────────────┘
```

> **Bezpieczeństwo.** Jeżeli mata jest zasilana z sieci 230 V, po stronie napięcia
> sieciowego pracuj wyłącznie przy odłączonym zasilaniu, zamknij wszystko w obudowie
> i użyj przewodów o odpowiednim przekroju. Program ma zabezpieczenia programowe,
> ale **nie zastępują one sprzętowego termostatu bezpieczeństwa** — patrz sekcja 3.

---

## 3. Termostat bezpieczeństwa (mocno zalecany)

Zabezpieczenia w programie (odcięcie powyżej 45 °C, limit 60 min grzania, wyłączenie
przy utracie czujnika) działają tylko wtedy, gdy ESP i przekaźnik są sprawne.
Nie pomogą w trzech realnych awariach:

| Awaria | Skutek | Czy program pomoże |
|---|---|---|
| Zespawane styki przekaźnika | mata grzeje mimo sygnału „wyłącz" | nie — uszkodzenie mechaniczne |
| Zawieszenie ESP przy włączonej macie | pętla stoi, przekaźnik trzyma | nie (restart tak, samo zawieszenie nie) |
| Czujnik odklei się od maty / wypadnie z terrarium | DS18B20 pokazuje 24 °C powietrza, gdy mata ma 60 °C | tylko częściowo — próg 45 °C nie zadziała, zostaje limit czasu grzania |

Trzeci przypadek zdarza się najczęściej. Dlatego w obwód zasilania maty warto wpiąć
**szeregowo element czysto fizyczny**, niezależny od mikrokontrolera:

```
230 V (L) ─► styk NO przekaźnika ─► termostat bimetaliczny NC ─► bezpiecznik ─► mata ─► N
                                    (rozwiera przy ~45 °C)      termiczny
```

### Co kupić

| Element | Czego szukać | Cena | Uwagi |
|---|---|---|---|
| Termostat bimetaliczny | `KSD9700`, **NC**, **40 lub 45 °C**, 5 A/250 V | ok. 4–8 zł | podstawowe zabezpieczenie, samoczynnie wraca po ostygnięciu |
| Bezpiecznik termiczny | 250 V / 10 A, **84 °C** (najniższy powszechnie dostępny) | ok. 5–10 zł | jednorazowy, ochrona przeciwpożarowa „ostatniej szansy" |
| Opcjonalnie: gotowy sterownik z alarmem | Inkbird ITC-306T lub ITC-308 | ok. 150–250 zł | drugi, w pełni niezależny termostat z własną sondą i alarmem |

**Krytyczne przy zakupie:** termostat bimetaliczny musi być w wersji **NC**
(*normally closed* — rozwiera się od ciepła). Wersje **NO** działają odwrotnie
i w tej roli są bezużyteczne. Sprzedawcy często mylą oznaczenia w tytułach ofert,
więc sprawdź opis. Prąd 5 A / 250 V wystarcza z ogromnym zapasem dla maty 10–30 W.

Gdzie szukać (linki do wyszukiwarek i stron producenta — pojedyncze oferty wygasają):

- [Allegro — KSD9700](https://allegro.pl/listing?string=ksd9700) (wybierz wariant „NC 45C" albo „NC 40C")
- [Allegro — bezpiecznik termiczny 10 A](https://allegro.pl/listing?string=bezpiecznik+termiczny+10a)
- [Inkbird ITC-306T — strona producenta](https://www.inkbird.com/products/temperature-controller-itc-306t) (wyjście tylko grzewcze, alarm górny i dolny)
- [Inkbird ITC-308 — strona producenta (PL)](https://www.inkbird.com/pl/products/temperature-controller-itc-308-wifi)

### Montaż i test

1. Termostat bimetaliczny przyklej **taśmą aluminiową do powierzchni maty** — ma mierzyć
   to, co się grzeje, nie powietrze. Nigdy nie zostawiaj go luzem.
2. Bezpiecznik termiczny wpina się szeregowo, w tym samym przewodzie fazowym.
3. Gotowy sterownik (wariant trzeci) łączy się kaskadowo: gniazdko → Inkbird
   (limit np. 33 °C) → przekaźnik ESP → mata. Grzanie wymaga wtedy zgody obu urządzeń.
4. **Test po montażu:** wyjmij DS18B20 z terrarium i połóż w chłodnym miejscu.
   Program będzie grzał w nieskończoność, a zabezpieczenie powinno odciąć matę.
   To jedyny sposób, żeby sprawdzić, czy naprawdę działa.

Progi dobieraj z zapasem 10–15 °C nad temperaturą zadaną: przy 28–30 °C w terrarium
bimetal 45 °C i bezpiecznik 84 °C nie będą przeszkadzać w normalnej pracy.

---

## 4. Wgranie programu

### Arduino IDE

1. **Plik → Preferencje → Dodatkowe adresy URL menedżera płytek**:
   `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
2. **Narzędzia → Płytka → Menedżer płytek** → zainstaluj **esp32** (Espressif Systems).
3. **Narzędzia → Płytka → ESP32 Arduino → XIAO_ESP32C3**.
4. **Szkic → Dołącz bibliotekę → Zarządzaj bibliotekami** → zainstaluj:
   - **OneWire** (Paul Stoffregen)
   - **DallasTemperature** (Miles Burton)
5. Otwórz `terrarium-thermostat.ino`, uzupełnij dane WiFi w `config.h`, wgraj na płytkę.

### PlatformIO

```bash
cd terrarium-thermostat
pio run -t upload
pio device monitor          # log pracy, 115200 baud
```

---

## 5. Konfiguracja (`config.h`)

Przed wgraniem ustaw co najmniej dane sieci:

```c
#define WIFI_SSID     "TwojaSiecWiFi"
#define WIFI_PASSWORD "TwojeHasloWiFi"
```

Jeśli moduł nie połączy się z siecią w 20 sekund, uruchomi **własny hotspot**
`Terrarium-Termostat` (hasło `terrarium123`) — wtedy wchodzisz na `http://192.168.4.1`.

Pozostałe pozycje w `config.h`: numery pinów, polaryzacja przekaźnika
(`RELAY_ACTIVE_HIGH` — ustaw `0` dla modułów wyzwalanych stanem niskim), nastawy
domyślne, progi bezpieczeństwa i czas pomiędzy pomiarami.

---

## 6. Obsługa przez przeglądarkę

Po starcie moduł wypisuje na porcie szeregowym swój adres IP. Wejdź na:

- `http://terrarium.local` (mDNS — działa m.in. na macOS, iOS, Windows 10+),
- albo bezpośrednio na adres IP z logu.

Strona pokazuje aktualną temperaturę, stan pracy, informację, czy mata grzeje,
oraz odliczanie do kolejnego pomiaru. Do ustawienia są:

| Nastawa | Zakres | Opis |
|---|---|---|
| Temperatura zadana | 10–40 °C | temperatura utrzymywana w terrarium |
| Histereza | 0,2–5 °C | o ile stopni poniżej zadanej ma ruszyć grzanie |
| Przerwa po dogrzaniu | 5–120 min | czas bez pomiarów po osiągnięciu zadanej |
| Termostat włączony | tak/nie | wyłączenie zatrzymuje grzanie, pomiary trwają dalej |

Nastawy zapisują się w pamięci nieulotnej (NVS) i przeżywają zanik zasilania.

---

## 7. Jak to działa

| Stan | Co się dzieje |
|---|---|
| **Czuwanie** | pomiar co 10 s; gdy temperatura spadnie do `zadana − histereza`, włącza się mata |
| **Grzanie** | pomiar co 10 s; po osiągnięciu temperatury zadanej mata gaśnie |
| **Przerwa** | mata wyłączona, przez ustawiony czas (min. 5 min) **żaden pomiar nie jest wykonywany** |
| **Awaria** | mata wyłączona; pomiary trwają, powrót do pracy jest automatyczny |

Przykładowy cykl przy zadanej 28 °C i histerezie 0,5 °C: grzanie startuje przy
27,5 °C, kończy się przy 28 °C, po czym przez 5 minut moduł „nie patrzy” na czujnik.
Po tym czasie od razu wykonuje pomiar i decyduje, czy grzać dalej.

Stan **awarii** włącza się, gdy:

- czujnik nie odpowiada przy trzech kolejnych próbach (`Brak odczytu z czujnika DS18B20`),
- temperatura przekroczy 45 °C (`SAFETY_MAX_C`) — powrót po spadku poniżej 40 °C,
- jeden cykl grzania trwa dłużej niż 60 minut (`MAX_HEATING_MINUTES`) — sygnał, że
  mata nie grzeje albo czujnik leży w złym miejscu.

---

## 8. API

| Metoda | Ścieżka | Opis |
|---|---|---|
| `GET` | `/` | strona sterująca |
| `GET` | `/api/status` | bieżący stan w formacie JSON |
| `POST` | `/api/settings` | zapis nastaw (`setpoint`, `hysteresis`, `rest`, `enabled`) |

```bash
curl http://terrarium.local/api/status
curl -X POST http://terrarium.local/api/settings -d "setpoint=29.5&hysteresis=0.5&rest=5&enabled=1"
```

Odpowiedź `/api/status`:

```json
{"temp":27.94,"hasReading":true,"tempAge":4,"setpoint":28.0,"hysteresis":0.5,
 "restMinutes":5,"enabled":true,"relay":true,"state":"HEATING","stateLabel":"grzanie",
 "stateClass":"heat","restRemaining":0,"nextMeasure":6,"fault":"",
 "uptime":3821,"rssi":-58,"ip":"192.168.0.42"}
```

Wartości spoza dozwolonych zakresów są przycinane do najbliższej dopuszczalnej,
więc błędne żądanie nie rozstroi termostatu.

---

## 9. Test logiki bez sprzętu

Katalog `test/` zawiera symulację: oryginalny szkic kompilowany na komputerze
z atrapami bibliotek Arduino i prostym modelem cieplnym terrarium.

```bash
cd terrarium-thermostat/test
./run.sh
```

Sprawdzane są: pełny cykl grzania, dotrzymanie 5-minutowej przerwy bez pomiarów,
dwie godziny pracy ciągłej, utrata czujnika, przegrzanie i wyłączenie termostatu.

---

## 10. Typowe problemy

| Objaw | Przyczyna |
|---|---|
| `nie znaleziono DS18B20` w logu | brak rezystora 4,7 kΩ, zamienione żyły albo zbyt długi przewód |
| Temperatura `--,-` na stronie | czujnik nie odpowiada — patrz wyżej |
| Mata grzeje odwrotnie, niż powinna | ustaw `RELAY_ACTIVE_HIGH` na `0` w `config.h` |
| Mata mruga przy starcie modułu | moduł przekaźnika wyzwalany stanem niskim — poza zmianą `RELAY_ACTIVE_HIGH` dodaj rezystor 10 kΩ z D2 do 3V3 |
| `terrarium.local` nie działa | system bez mDNS — użyj adresu IP z portu szeregowego |
| Strona nie odświeża się | moduł stracił WiFi; sprawdź zasięg, ESP łączy się ponownie samo |
