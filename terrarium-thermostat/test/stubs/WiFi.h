#pragma once
#include "Arduino.h"
#define WL_CONNECTED 3
enum wifi_mode_t { WIFI_OFF, WIFI_STA, WIFI_AP, WIFI_AP_STA };
class IPAddressStub { public: String toString() const { return String(); } };
class WiFiClass {
public:
  void mode(wifi_mode_t){}
  wifi_mode_t getMode(){ return WIFI_STA; }
  void setAutoReconnect(bool){}
  void setSleep(bool){}
  void begin(const char*, const char*){}
  int status(){ return 0; }
  IPAddressStub localIP(){ return IPAddressStub(); }
  IPAddressStub softAPIP(){ return IPAddressStub(); }
  bool softAP(const char*, const char*){ return true; }
  int RSSI(){ return 0; }
};
extern WiFiClass WiFi;
