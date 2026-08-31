#pragma once
#include "Arduino.h"
#define HTTP_GET 1
#define HTTP_POST 2
class WebServer {
public:
  WebServer(int){}
  void on(const char*, int, void(*)()){}
  void onNotFound(void(*)()){}
  void begin(){}
  void handleClient(){}
  void sendHeader(const char*, const char*){}
  void send(int, const char*, const String&){}
  void send(int, const char*, const char*){}
  void send_P(int, const char*, const char*){}
  bool hasArg(const char*){ return false; }
  String arg(const char*){ return String(); }
};
