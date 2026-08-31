#!/usr/bin/env bash
# Kompiluje i uruchamia symulację logiki termostatu (bez sprzętu).
set -euo pipefail
cd "$(dirname "$0")"
g++ -std=gnu++17 -Istubs -o /tmp/test_termostat test_termostat.cpp
/tmp/test_termostat
