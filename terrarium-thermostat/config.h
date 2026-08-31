/*
 * config.h — wszystkie ustawienia użytkownika w jednym miejscu.
 * Po zmianach wgraj szkic ponownie na płytkę.
 */

#pragma once

/* ---------------------------------------------------------------
 * 1. Sieć WiFi
 * --------------------------------------------------------------- */

// Dane Twojej sieci domowej. Jeśli ESP nie zdoła się połączyć,
// samo uruchomi własny hotspot (dane niżej).
#define WIFI_SSID                 "TwojaSiecWiFi"
#define WIFI_PASSWORD             "TwojeHasloWiFi"
#define WIFI_CONNECT_TIMEOUT_MS   20000UL

// Awaryjny punkt dostępowy — gdy nie ma sieci domowej.
// Połącz się z tą siecią telefonem i wejdź na http://192.168.4.1
#define AP_SSID                   "Terrarium-Termostat"
#define AP_PASSWORD               "terrarium123"   // min. 8 znaków

// Adres w sieci lokalnej: http://terrarium.local
#define MDNS_HOSTNAME             "terrarium"

/* ---------------------------------------------------------------
 * 2. Piny (numeracja GPIO układu ESP32-C3, nie oznaczenia Dx)
 * --------------------------------------------------------------- */

#define PIN_ONEWIRE               3    // D1 — DS18B20 (DQ) + rezystor 4,7 kΩ do 3V3
#define PIN_RELAY                 4    // D2 — wejście IN modułu przekaźnika

// 1 — przekaźnik załącza się stanem wysokim,
// 0 — przekaźnik załącza się stanem niskim (typowe moduły z optoizolacją).
#define RELAY_ACTIVE_HIGH         1

/* ---------------------------------------------------------------
 * 3. Nastawy domyślne (przy pierwszym starcie; potem z pamięci NVS)
 * --------------------------------------------------------------- */

#define DEFAULT_SETPOINT_C        28.0f   // temperatura zadana
#define DEFAULT_HYSTERESIS_C      0.5f    // grzanie startuje przy zadana − histereza
#define DEFAULT_REST_MINUTES      5       // przerwa po dogrzaniu (wymóg: min. 5 min)
#define DEFAULT_ENABLED           true    // termostat aktywny

/* ---------------------------------------------------------------
 * 4. Zakresy dopuszczalne dla nastaw z przeglądarki
 * --------------------------------------------------------------- */

#define SETPOINT_MIN_C            10.0f
#define SETPOINT_MAX_C            40.0f
#define HYSTERESIS_MIN_C          0.2f
#define HYSTERESIS_MAX_C          5.0f
#define REST_MIN_MINUTES          5       // krócej niż 5 min nie pozwalamy ustawić
#define REST_MAX_MINUTES          120

/* ---------------------------------------------------------------
 * 5. Bezpieczeństwo i czasy pracy
 * --------------------------------------------------------------- */

#define SAFETY_MAX_C              45.0f   // powyżej — awaryjne odcięcie maty
#define SAFETY_RECOVER_C          40.0f   // powrót do pracy po schłodzeniu poniżej
#define MAX_HEATING_MINUTES       60      // maksymalny czas jednego cyklu grzania
#define MEASURE_INTERVAL_MS       10000UL // co ile mierzyć w trybie normalnym
#define SENSOR_ERRORS_TO_FAULT    3       // ile błędnych odczytów pod rząd = awaria
#define DS18B20_RESOLUTION_BITS   12      // 12 bitów = 0,0625 °C, konwersja ~750 ms
