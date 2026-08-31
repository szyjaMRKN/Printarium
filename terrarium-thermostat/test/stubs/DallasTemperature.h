#pragma once
#include "OneWire.h"
#define DEVICE_DISCONNECTED_C -127.0f
typedef uint8_t DeviceAddress[8];
class DallasTemperature {
public:
  DallasTemperature(OneWire*){}
  void begin(){}
  void setWaitForConversion(bool){}
  bool getAddress(uint8_t*, uint8_t){ return true; }
  void setResolution(const uint8_t*, uint8_t){}
  uint16_t millisToWaitForConversion(uint8_t){ return 750; }
  bool requestTemperaturesByAddress(const uint8_t*){ return true; }
  float getTempC(const uint8_t*);
};
