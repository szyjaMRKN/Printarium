/*
 * test_termostat.cpp — symulacja logiki termostatu na komputerze.
 *
 * Dołącza oryginalny szkic (terrarium-thermostat.ino) i podstawia pod niego
 * atrapy bibliotek Arduino (katalog stubs/) oraz prosty model cieplny
 * terrarium. Pozwala sprawdzić maszynę stanów bez podłączania sprzętu.
 *
 * Uruchomienie:  ./run.sh
 */
#include <cstdio>
#include "Arduino.h"
#include "WiFi.h"
#include "ESPmDNS.h"

static unsigned long g_now  = 0;
static float         g_temp = 22.0f;
static bool          g_relayPin = false;
static bool          g_sensorOk = true;
static bool          g_hold = false;   // zamrozenie modelu cieplnego w tescie

unsigned long millis() { return g_now; }
void delay(unsigned long ms) { g_now += ms; }
void pinMode(int, int) {}
void digitalWrite(int pin, int val);

SerialC   Serial;
WiFiClass WiFi;
MDNSClass MDNS;

#include "../terrarium-thermostat.ino"

float DallasTemperature::getTempC(const uint8_t*) { return g_sensorOk ? g_temp : DEVICE_DISCONNECTED_C; }
void digitalWrite(int pin, int val) { if (pin == PIN_RELAY) g_relayPin = (val == HIGH); }

static const char* nazwa(State s) {
  switch (s) { case ST_IDLE: return "CZUWANIE"; case ST_HEATING: return "GRZANIE";
               case ST_REST: return "PRZERWA"; default: return "AWARIA"; }
}

static int bledy = 0;
static void sprawdz(bool ok, const char* opis) {
  printf("  [%s] %s\n", ok ? " OK " : "BLAD", opis);
  if (!ok) bledy++;
}

// Krok symulacji: prosty model cieplny + loop() szkicu.
static void krok(uint32_t ms) {
  for (uint32_t i = 0; i < ms / 100; i++) {
    g_now += 100;
    if (!g_hold) {
      if (g_relayPin) g_temp += 0.002f;                     // mata: ~0,02 C/s
      else            g_temp += (21.0f - g_temp) * 0.0004f; // chlodzenie ku 21 C
    }
    loop();
  }
}

int main() {
  setup();
  printf("Nastawy: zadana=%.1f C, histereza=%.1f C, przerwa=%u min\n\n",
         cfg.setpoint, cfg.hysteresis, cfg.restMinutes);

  /* --- 1. Pelen cykl: grzanie -> przerwa 5 min bez pomiarow -------------- */
  printf("1. Cykl grzania i przerwy\n");
  krok(60000);
  sprawdz(state == ST_HEATING && g_relayPin, "zimne terrarium (22 C) -> mata wlaczona");

  while (state == ST_HEATING) krok(1000);
  sprawdz(state == ST_REST && !g_relayPin, "po osiagnieciu zadanej -> przerwa, mata wylaczona");
  sprawdz(lastTemp >= cfg.setpoint, "wylaczenie dopiero po osiagnieciu zadanej");

  uint32_t restStart = g_now, readAtRestStart = lastReadAt;
  float tempAtRestStart = lastTemp;
  while (state == ST_REST) krok(1000);
  uint32_t trwanie = g_now - restStart;
  sprawdz(trwanie >= 5UL * 60000UL, "przerwa trwala co najmniej 5 minut");
  printf("       (dokladnie %.2f min)\n", trwanie / 60000.0);
  sprawdz(lastReadAt == readAtRestStart && lastTemp == tempAtRestStart,
          "w trakcie przerwy nie wykonano zadnego pomiaru");

  krok(15000);
  sprawdz(lastReadAt > readAtRestStart, "po przerwie pomiary ruszaja od razu");

  /* --- 2. Utrzymanie temperatury (2 h) ----------------------------------- */
  printf("\n2. Praca ciagla przez 2 godziny\n");
  float tmin = 99, tmax = -99; int cykle = 0; State prev = state;
  for (uint32_t i = 0; i < 7200; i++) {
    krok(1000);
    if (g_temp < tmin) tmin = g_temp;
    if (g_temp > tmax) tmax = g_temp;
    if (state == ST_REST && prev == ST_HEATING) cykle++;
    if (state == ST_REST && g_relayPin) { printf("  [BLAD] mata wlaczona w przerwie\n"); bledy++; }
    prev = state;
  }
  printf("       zakres temperatury %.2f–%.2f C, cykli grzania: %d\n", tmin, tmax, cykle);
  sprawdz(tmax < SAFETY_MAX_C, "temperatura nie przekroczyla progu bezpieczenstwa");
  sprawdz(cykle > 0 && cykle <= 24, "liczba zalaczen przekaznika rozsadna (max 12/h)");

  /* --- 3. Utrata czujnika ------------------------------------------------ */
  printf("\n3. Odlaczenie czujnika DS18B20\n");
  while (state != ST_HEATING) krok(1000);
  g_sensorOk = false;
  krok(60000);
  sprawdz(state == ST_FAULT, "brak odczytow -> stan awarii");
  sprawdz(!g_relayPin, "mata wylaczona w awarii");
  g_sensorOk = true;
  krok(30000);
  sprawdz(state != ST_FAULT, "po powrocie czujnika termostat wraca do pracy");

  /* --- 4. Przegrzanie ---------------------------------------------------- */
  printf("\n4. Przekroczenie temperatury bezpieczenstwa\n");
  g_hold = true;
  g_temp = SAFETY_MAX_C + 1.0f;
  krok(30000);
  sprawdz(state == ST_FAULT && !g_relayPin, "temperatura > progu -> awaryjne odciecie maty");
  g_temp = SAFETY_RECOVER_C + 1.0f;
  krok(30000);
  sprawdz(state == ST_FAULT, "przy wciaz wysokiej temperaturze awaria trwa");
  g_temp = 26.0f;
  krok(30000);
  sprawdz(state != ST_FAULT, "po schlodzeniu powrot do normalnej pracy");
  g_hold = false;

  /* --- 5. Wylaczenie termostatu z przegladarki --------------------------- */
  printf("\n5. Wylaczenie termostatu\n");
  while (state != ST_HEATING) krok(1000);
  cfg.enabled = false;
  setRelay(false);
  if (state == ST_HEATING) enterState(ST_IDLE);
  krok(120000);
  sprawdz(!g_relayPin && state == ST_IDLE, "mata pozostaje wylaczona mimo niskiej temperatury");
  sprawdz(lastReadAt > g_now - 20000, "pomiary trwaja dalej (podglad temperatury)");
  cfg.enabled = true;
  krok(15000);
  sprawdz(state == ST_HEATING, "po ponownym wlaczeniu grzanie wraca");

  /* --- 6. Awaria czujnika przy wysokiej (ale bezpiecznej) temperaturze --- */
  printf("\n6. Utrata czujnika przy 42 C — powrot nie czeka na prog schladzania\n");
  g_hold = true;
  g_temp = 42.0f;              // powyzej progu powrotu po przegrzaniu (40 C)
  g_sensorOk = false;
  krok(60000);
  sprawdz(state == ST_FAULT && !g_relayPin, "brak czujnika -> awaria, mata wylaczona");
  g_sensorOk = true;
  krok(30000);
  sprawdz(state != ST_FAULT, "po powrocie czujnika brak blokady progiem przegrzania");
  g_hold = false;

  printf("\n=== Bledow: %d ===\n", bledy);
  return bledy == 0 ? 0 : 1;
}
