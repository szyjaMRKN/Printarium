/*
 * Termostat terrarium — Seeed Studio XIAO ESP32-C3
 * -------------------------------------------------
 * Czujnik DS18B20 mierzy temperaturę w terrarium, przekaźnik załącza matę
 * grzewczą. Podgląd i nastawy przez przeglądarkę (http://terrarium.local).
 *
 * Zasada działania:
 *   CZUWANIE  — pomiar co 10 s; gdy temperatura spadnie do (zadana − histereza)
 *               włącza się mata.
 *   GRZANIE   — pomiar co 10 s; gdy temperatura osiągnie zadaną, mata gaśnie.
 *   PRZERWA   — po dogrzaniu przez 5 minut (wartość konfigurowalna) NIE jest
 *               wykonywany żaden pomiar, a mata pozostaje wyłączona; dzięki temu
 *               ciepło rozchodzi się po terrarium i przekaźnik nie „klika”.
 *   AWARIA    — brak czujnika, przekroczona temperatura bezpieczeństwa albo zbyt
 *               długie grzanie: mata wyłączona, pomiary trwają dalej, powrót do
 *               pracy następuje automatycznie po ustąpieniu przyczyny.
 *
 * Biblioteki (Menedżer bibliotek Arduino IDE):
 *   - OneWire (Paul Stoffregen)
 *   - DallasTemperature (Miles Burton)
 * Płytka: „XIAO_ESP32C3” z pakietu esp32 (Espressif Systems).
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <Preferences.h>
#include <OneWire.h>
#include <DallasTemperature.h>

#include "config.h"
#include "web_page.h"

/* --------------------------------------------------------------------------
 * Obiekty globalne
 * -------------------------------------------------------------------------- */

OneWire            oneWire(PIN_ONEWIRE);
DallasTemperature  sensors(&oneWire);
DeviceAddress      sensorAddress;
WebServer          server(80);
Preferences        prefs;

/* --------------------------------------------------------------------------
 * Stan termostatu
 * -------------------------------------------------------------------------- */

enum State : uint8_t { ST_IDLE, ST_HEATING, ST_REST, ST_FAULT };

struct Settings {
  float    setpoint;
  float    hysteresis;
  uint16_t restMinutes;
  bool     enabled;
};

Settings cfg = {
  DEFAULT_SETPOINT_C, DEFAULT_HYSTERESIS_C, DEFAULT_REST_MINUTES, DEFAULT_ENABLED
};

State    state           = ST_IDLE;
uint32_t stateSince      = 0;       // millis() wejścia w bieżący stan
uint32_t heatingSince    = 0;       // millis() załączenia maty
bool     relayOn         = false;

float    lastTemp        = 0.0f;
bool     hasReading      = false;   // czy mamy jakikolwiek poprawny odczyt
uint32_t lastReadAt      = 0;
uint8_t  errorStreak     = 0;
String   faultMessage    = "";
bool     overheatFault   = false;   // awaria z przegrzania wymaga schlodzenia

bool     sensorFound     = false;
bool     conversionPending = false;
uint32_t conversionReadyAt = 0;
uint32_t nextMeasureAt   = 0;
uint32_t conversionMs    = 800;

/* --------------------------------------------------------------------------
 * Pomocnicze
 * -------------------------------------------------------------------------- */

static inline bool timeReached(uint32_t now, uint32_t deadline) {
  return (int32_t)(now - deadline) >= 0;   // odporne na przepełnienie millis()
}

float clampF(float v, float lo, float hi) { return v < lo ? lo : (v > hi ? hi : v); }
long  clampL(long v, long lo, long hi)    { return v < lo ? lo : (v > hi ? hi : v); }

uint32_t restMillis() { return (uint32_t)cfg.restMinutes * 60000UL; }

void setRelay(bool on) {
  relayOn = on;
#if RELAY_ACTIVE_HIGH
  digitalWrite(PIN_RELAY, on ? HIGH : LOW);
#else
  digitalWrite(PIN_RELAY, on ? LOW : HIGH);
#endif
}

void enterState(State s) {
  state = s;
  stateSince = millis();
}

void raiseFault(const char *msg) {
  setRelay(false);
  faultMessage = msg;
  enterState(ST_FAULT);
  Serial.printf("[AWARIA] %s\n", msg);
}

void clearFault() {
  if (faultMessage.length()) Serial.println("[AWARIA] przyczyna ustapila");
  faultMessage = "";
}

/* --------------------------------------------------------------------------
 * Nastawy w pamięci nieulotnej
 * -------------------------------------------------------------------------- */

void loadSettings() {
  prefs.begin("termostat", true);
  cfg.setpoint    = prefs.getFloat("sp",   DEFAULT_SETPOINT_C);
  cfg.hysteresis  = prefs.getFloat("hys",  DEFAULT_HYSTERESIS_C);
  cfg.restMinutes = prefs.getUShort("rest", DEFAULT_REST_MINUTES);
  cfg.enabled     = prefs.getBool("en",    DEFAULT_ENABLED);
  prefs.end();

  cfg.setpoint    = clampF(cfg.setpoint,   SETPOINT_MIN_C,   SETPOINT_MAX_C);
  cfg.hysteresis  = clampF(cfg.hysteresis, HYSTERESIS_MIN_C, HYSTERESIS_MAX_C);
  cfg.restMinutes = (uint16_t)clampL(cfg.restMinutes, REST_MIN_MINUTES, REST_MAX_MINUTES);
}

void saveSettings() {
  prefs.begin("termostat", false);
  prefs.putFloat("sp",    cfg.setpoint);
  prefs.putFloat("hys",   cfg.hysteresis);
  prefs.putUShort("rest", cfg.restMinutes);
  prefs.putBool("en",     cfg.enabled);
  prefs.end();
}

/* --------------------------------------------------------------------------
 * Logika termostatu — wywoływana po każdym nowym odczycie
 * -------------------------------------------------------------------------- */

void onReading(float t, uint32_t now) {
  lastTemp   = t;
  hasReading = true;
  lastReadAt = now;
  errorStreak = 0;

  // 1. Zabezpieczenie przed przegrzaniem — ważniejsze niż wszystko inne.
  if (t >= SAFETY_MAX_C) {
    const char *MSG = "Przekroczona temperatura bezpieczenstwa — mata odcieta";
    overheatFault = true;
    if (state != ST_FAULT) {
      raiseFault(MSG);
    } else {                       // awaria juz trwa — uaktualniamy tylko przyczyne
      setRelay(false);
      faultMessage = MSG;
    }
    return;
  }

  // 2. Termostat wyłączony z poziomu przeglądarki — tylko monitorujemy.
  if (!cfg.enabled) {
    setRelay(false);
    if (state != ST_IDLE) { clearFault(); enterState(ST_IDLE); }
    return;
  }

  // 3. Wyjście z awarii, gdy czujnik znów odpowiada i jest bezpiecznie.
  if (state == ST_FAULT) {
    if (overheatFault && t > SAFETY_RECOVER_C) return;   // jeszcze za gorąco
    overheatFault = false;
    clearFault();
    enterState(ST_IDLE);
  }

  switch (state) {
    case ST_IDLE:
      if (t <= cfg.setpoint - cfg.hysteresis) {
        setRelay(true);
        heatingSince = now;
        enterState(ST_HEATING);
        Serial.printf("[GRZANIE] start przy %.2f C (zadana %.2f C)\n", t, cfg.setpoint);
      }
      break;

    case ST_HEATING:
      if (t >= cfg.setpoint) {
        setRelay(false);
        enterState(ST_REST);
        Serial.printf("[GRZANIE] osiagnieto %.2f C — przerwa %u min\n", t, cfg.restMinutes);
      } else if (timeReached(now, heatingSince + (uint32_t)MAX_HEATING_MINUTES * 60000UL)) {
        raiseFault("Zbyt dlugie grzanie — sprawdz mate i czujnik");
      }
      break;

    case ST_REST:   // w tym stanie pomiary w ogóle nie są wykonywane
    case ST_FAULT:
      break;
  }
}

void onSensorError(uint32_t now) {
  (void)now;                       // lastReadAt = czas ostatniego UDANEGO pomiaru
  if (errorStreak < 255) errorStreak++;
  if (errorStreak >= SENSOR_ERRORS_TO_FAULT && state != ST_FAULT) {
    overheatFault = false;
    raiseFault("Brak odczytu z czujnika DS18B20");
  }
}

/* --------------------------------------------------------------------------
 * Obsługa czujnika — nieblokująca (konwersja DS18B20 trwa ~750 ms)
 * -------------------------------------------------------------------------- */

void setupSensor() {
  sensors.begin();
  sensors.setWaitForConversion(false);          // nie blokujemy pętli i serwera
  sensorFound = sensors.getAddress(sensorAddress, 0);
  if (sensorFound) {
    sensors.setResolution(sensorAddress, DS18B20_RESOLUTION_BITS);
    Serial.println("[CZUJNIK] DS18B20 wykryty");
  } else {
    Serial.println("[CZUJNIK] nie znaleziono DS18B20 — sprawdz podlaczenie i rezystor 4,7 kOhm");
  }
  conversionMs = sensors.millisToWaitForConversion(DS18B20_RESOLUTION_BITS) + 50;
}

void sensorTick(uint32_t now) {
  if (state == ST_REST) return;        // w przerwie po dogrzaniu nie mierzymy

  if (!conversionPending) {
    if (!timeReached(now, nextMeasureAt)) return;

    if (!sensorFound) {                          // próba ponownego wykrycia
      sensors.begin();
      sensorFound = sensors.getAddress(sensorAddress, 0);
      if (sensorFound) sensors.setResolution(sensorAddress, DS18B20_RESOLUTION_BITS);
      if (!sensorFound) {
        nextMeasureAt = now + MEASURE_INTERVAL_MS;
        onSensorError(now);
        return;
      }
    }

    sensors.requestTemperaturesByAddress(sensorAddress);
    conversionPending = true;
    conversionReadyAt = now + conversionMs;
    return;
  }

  if (!timeReached(now, conversionReadyAt)) return;

  float t = sensors.getTempC(sensorAddress);
  conversionPending = false;
  nextMeasureAt = now + MEASURE_INTERVAL_MS;

  if (t == DEVICE_DISCONNECTED_C || t < -55.0f || t > 125.0f) {
    sensorFound = false;
    onSensorError(now);
  } else {
    onReading(t, now);
  }
}

/* --------------------------------------------------------------------------
 * API HTTP
 * -------------------------------------------------------------------------- */

uint32_t restRemainingSec(uint32_t now) {
  if (state != ST_REST) return 0;
  uint32_t elapsed = now - stateSince;
  return elapsed >= restMillis() ? 0 : (restMillis() - elapsed + 999) / 1000;
}

uint32_t nextMeasureSec(uint32_t now) {
  if (state == ST_REST) return restRemainingSec(now);
  if (conversionPending) return 0;
  return timeReached(now, nextMeasureAt) ? 0 : (nextMeasureAt - now + 999) / 1000;
}

const char *stateCode() {
  switch (state) {
    case ST_HEATING: return "HEATING";
    case ST_REST:    return "REST";
    case ST_FAULT:   return "FAULT";
    default:         return "IDLE";
  }
}

const char *stateLabel() {
  if (state == ST_FAULT)   return "awaria";
  if (!cfg.enabled)        return "wylaczony";
  if (state == ST_HEATING) return "grzanie";
  if (state == ST_REST)    return "przerwa";
  return "czuwanie";
}

const char *stateClass() {
  if (state == ST_FAULT)   return "fault";
  if (!cfg.enabled)        return "";
  if (state == ST_HEATING) return "heat";
  if (state == ST_REST)    return "rest";
  return "idle";
}

String statusJson() {
  uint32_t now = millis();
  String ip = (WiFi.getMode() == WIFI_AP) ? WiFi.softAPIP().toString() : WiFi.localIP().toString();

  char buf[512];
  snprintf(buf, sizeof(buf),
    "{\"temp\":%.2f,\"hasReading\":%s,\"tempAge\":%lu,"
    "\"setpoint\":%.1f,\"hysteresis\":%.1f,\"restMinutes\":%u,\"enabled\":%s,"
    "\"relay\":%s,\"state\":\"%s\",\"stateLabel\":\"%s\",\"stateClass\":\"%s\","
    "\"restRemaining\":%lu,\"nextMeasure\":%lu,\"fault\":\"%s\","
    "\"uptime\":%lu,\"rssi\":%d,\"ip\":\"%s\"}",
    lastTemp,
    hasReading ? "true" : "false",
    hasReading ? (unsigned long)((now - lastReadAt) / 1000) : 0UL,
    cfg.setpoint, cfg.hysteresis, cfg.restMinutes,
    cfg.enabled ? "true" : "false",
    relayOn ? "true" : "false",
    stateCode(), stateLabel(), stateClass(),
    (unsigned long)restRemainingSec(now),
    (unsigned long)nextMeasureSec(now),
    faultMessage.c_str(),
    (unsigned long)(now / 1000),
    (int)WiFi.RSSI(),
    ip.c_str());

  return String(buf);
}

void handleRoot() {
  server.sendHeader("Cache-Control", "no-store");
  server.send_P(200, "text/html; charset=utf-8", INDEX_HTML);
}

void handleStatus() {
  server.sendHeader("Cache-Control", "no-store");
  server.send(200, "application/json", statusJson());
}

void handleSettings() {
  bool changed = false;

  if (server.hasArg("setpoint")) {
    cfg.setpoint = clampF(server.arg("setpoint").toFloat(), SETPOINT_MIN_C, SETPOINT_MAX_C);
    changed = true;
  }
  if (server.hasArg("hysteresis")) {
    cfg.hysteresis = clampF(server.arg("hysteresis").toFloat(), HYSTERESIS_MIN_C, HYSTERESIS_MAX_C);
    changed = true;
  }
  if (server.hasArg("rest")) {
    cfg.restMinutes = (uint16_t)clampL(server.arg("rest").toInt(), REST_MIN_MINUTES, REST_MAX_MINUTES);
    changed = true;
  }
  if (server.hasArg("enabled")) {
    String v = server.arg("enabled");
    cfg.enabled = (v == "1" || v == "true" || v == "on");
    changed = true;
  }

  if (!changed) {
    server.send(400, "application/json", "{\"error\":\"brak nastaw\"}");
    return;
  }

  saveSettings();

  // Wyłączenie termostatu działa natychmiast, bez czekania na kolejny pomiar.
  if (!cfg.enabled) {
    setRelay(false);
    if (state == ST_HEATING) enterState(ST_IDLE);
  }

  Serial.printf("[NASTAWY] zadana %.1f C, histereza %.1f C, przerwa %u min, %s\n",
                cfg.setpoint, cfg.hysteresis, cfg.restMinutes,
                cfg.enabled ? "wlaczony" : "wylaczony");

  server.sendHeader("Cache-Control", "no-store");
  server.send(200, "application/json", statusJson());
}

void handleNotFound() {
  server.send(404, "text/plain; charset=utf-8", "Nie znaleziono");
}

/* --------------------------------------------------------------------------
 * Sieć
 * -------------------------------------------------------------------------- */

void setupWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.setSleep(false);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.printf("[WIFI] laczenie z \"%s\"", WIFI_SSID);
  uint32_t start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < WIFI_CONNECT_TIMEOUT_MS) {
    delay(250);
    Serial.print(".");
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("[WIFI] polaczono, IP: %s\n", WiFi.localIP().toString().c_str());
  } else {
    // Bez sieci domowej stawiamy własny hotspot — termostat pozostaje sterowalny.
    WiFi.mode(WIFI_AP);
    WiFi.softAP(AP_SSID, AP_PASSWORD);
    Serial.printf("[WIFI] brak sieci — hotspot \"%s\", IP: %s\n",
                  AP_SSID, WiFi.softAPIP().toString().c_str());
  }

  if (MDNS.begin(MDNS_HOSTNAME)) {
    MDNS.addService("http", "tcp", 80);
    Serial.printf("[WIFI] adres lokalny: http://%s.local\n", MDNS_HOSTNAME);
  }
}

/* --------------------------------------------------------------------------
 * setup / loop
 * -------------------------------------------------------------------------- */

void setup() {
  // Najpierw stan spoczynkowy przekaźnika, dopiero potem tryb wyjścia —
  // dzięki temu mata nie załącza się na moment podczas startu modułu.
#if RELAY_ACTIVE_HIGH
  digitalWrite(PIN_RELAY, LOW);
#else
  digitalWrite(PIN_RELAY, HIGH);
#endif
  pinMode(PIN_RELAY, OUTPUT);
  setRelay(false);

  Serial.begin(115200);
  delay(300);
  Serial.println("\n=== Termostat terrarium (XIAO ESP32-C3) ===");

  loadSettings();
  setupSensor();
  setupWifi();

  server.on("/", HTTP_GET, handleRoot);
  server.on("/api/status", HTTP_GET, handleStatus);
  server.on("/api/settings", HTTP_POST, handleSettings);
  server.on("/api/settings", HTTP_GET, handleSettings);   // wygodne do testów w pasku adresu
  server.onNotFound(handleNotFound);
  server.begin();
  Serial.println("[HTTP] serwer uruchomiony na porcie 80");

  enterState(ST_IDLE);
  nextMeasureAt = millis();     // pierwszy pomiar od razu po starcie
}

void loop() {
  server.handleClient();

  uint32_t now = millis();

  // Przerwa po dogrzaniu: mata wyłączona i — zgodnie z założeniem —
  // przez pełne 5 minut nie wykonujemy żadnego pomiaru.
  if (state == ST_REST) {
    if (relayOn) setRelay(false);
    if (timeReached(now, stateSince + restMillis())) {
      enterState(ST_IDLE);
      nextMeasureAt = now;     // po przerwie mierzymy natychmiast
      Serial.println("[PRZERWA] koniec — wracam do pomiarow");
    }
    return;
  }

  sensorTick(now);
}
