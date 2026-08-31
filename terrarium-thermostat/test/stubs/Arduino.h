#pragma once
#include <cstdint>
#include <cstdio>
#include <cstdarg>
#include <cstring>
#include <string>
#define PROGMEM
#define HIGH 1
#define LOW 0
#define OUTPUT 1
typedef uint8_t byte;
class String {
public:
  String(){} String(const char*){} String(const std::string&){}
  const char* c_str() const { return ""; }
  unsigned length() const { return 0; }
  float toFloat() const { return 0; }
  long toInt() const { return 0; }
  bool operator==(const char*) const { return false; }
  String& operator=(const char*) { return *this; }
};
class SerialC {
public:
  void begin(unsigned long){}
  void print(const char* s){ fputs(s, stdout); }
  void println(const char* s){ puts(s); }
  void println(){ puts(""); }
  int printf(const char* f, ...){ va_list a; va_start(a,f); int n=vprintf(f,a); va_end(a); return n; }
};
extern SerialC Serial;
unsigned long millis();
void delay(unsigned long);
void pinMode(int,int);
void digitalWrite(int,int);
