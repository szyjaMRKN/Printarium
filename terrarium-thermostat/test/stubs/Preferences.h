#pragma once
#include "Arduino.h"
class Preferences {
public:
  bool begin(const char*, bool){ return true; }
  void end(){}
  float getFloat(const char*, float d){ return d; }
  unsigned short getUShort(const char*, unsigned short d){ return d; }
  bool getBool(const char*, bool d){ return d; }
  void putFloat(const char*, float){}
  void putUShort(const char*, unsigned short){}
  void putBool(const char*, bool){}
};
