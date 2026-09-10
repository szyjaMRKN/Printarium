# Kalkulator kabla grzewczego — dobór rezystancji

Jednoplikowa aplikacja (`index.html`, bez zależności i bez budowania) pomagająca
wybrać właściwy wariant rezystancji kabla grzewczego na aukcji. Podajesz długość
odcinka i napięcie zasilania, a kalkulator wskazuje, które **Ω/m** dadzą zadaną
moc grzewczą.

Otwórz `index.html` w przeglądarce — to wszystko.

---

## 1. Wzory

Sprzedawca podaje rezystancję **na metr**, więc rezystancja odcinka to `L × R`:

| Wielkość | Wzór | Jednostka |
| --- | --- | --- |
| Moc łączna | `P = U² / (L × R)` | W |
| Moc na metr | `P/m = U² / (L² × R)` | W/m |
| Szukana rezystancja | `R = U² / (L² × P/m)` | Ω/m |

gdzie `U` — napięcie [V], `L` — długość odcinka [m], `R` — rezystancja [Ω/m].

Kontrola zgodności z rachunkiem sprzedawcy:

```
12 V, 0,5 m, 50 Ω/m  →  144 / (0,5 × 50) = 5,76 W  →  5,76 / 0,5 = 11,52 W/m
 5 V, 0,5 m, 10 Ω/m  →   25 / (0,5 × 10) = 5,00 W  →  5,00 / 0,5 = 10,00 W/m
```

Kalkulator odwraca ten rachunek: zamiast liczyć moc dla znanej rezystancji,
szuka rezystancji dla zadanej mocy.

## 2. Co robi aplikacja

- dobiera najbliższy dostępny wariant Ω/m (ranking po odległości logarytmicznej
  od celu, więc odchyłka w górę i w dół waży tak samo) oraz pokazuje drugi wybór;
- liczy moc na metr, moc łączną, pobór prądu, rezystancję odcinka i minimalny
  prąd zasilacza (z 30% zapasem);
- pokazuje tabelę wszystkich wariantów z paskiem odchyłki od celu; warianty
  bardzo odległe od celu są domyślnie zwinięte;
- podpowiada, jaka długość odcinka trafiłaby w cel dokładnie przy wybranym
  wariancie;
- ostrzega o wysokim poborze prądu, spadku napięcia przy 5 V i o mocy na metr
  zbyt dużej dla kabla bez odprowadzania ciepła;
- zapamiętuje ustawienia i listę wariantów w `localStorage`.

## 3. Założenia i ograniczenia

- **Rezystancja jest na metr.** Cały rachunek zakłada, że „50 Ω" w opisie aukcji
  oznacza 50 Ω/m — tak liczy sprzedawca. Jeśli wariant opisuje rezystancję
  gotowego odcinka, wzory są inne.
- **Rezystancja jest stała.** Pominięty jest temperaturowy współczynnik
  rezystancji oraz rezystancja przewodów doprowadzających.
- **Moc przy 100% wypełnienia.** Przy sterowaniu termostatem (PWM lub przekaźnik)
  moc średnia będzie niższa.
- Domyślna lista wariantów to typowy zestaw, a nie oferta konkretnej aukcji —
  podmień ją na wartości z rozwijanego menu sprzedawcy.

## 4. Struktura

```
kalkulator-kabla-grzewczego/
└── index.html   # cała aplikacja: znaczniki, style i logika
```

Fonty (Archivo, IBM Plex Sans, IBM Plex Mono) ładowane są z Google Fonts;
bez dostępu do sieci aplikacja działa normalnie, tylko na krojach zastępczych.
