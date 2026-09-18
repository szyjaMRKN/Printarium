# -*- coding: utf-8 -*-
"""Polecenia administracyjne uruchamiane z panelu — zamiast wiersza poleceń.

Na hostingu bez SSH jedyną drogą do `app.cli` jest pole
*Aplikacje Python → Wykonaj skrypt Python*. Panel potrafi przekazać argumenty,
więc wpisujesz tam na przykład:

    konsola.py migrate
    konsola.py list-users
    konsola.py reset-password --login admin --password NoweHaslo123
    konsola.py auto-backup
    konsola.py backup

Hasło trzeba podać w argumencie `--password`, bo panel nie pozwala odpowiadać
na pytania skryptu. Po zmianie hasła wyczyść pole polecenia w panelu, żeby
nie zostało zapisane w konfiguracji aplikacji.
"""

from __future__ import print_function

import os
import sys

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(APP_ROOT, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault("APP_ENV", "production")

if sys.version_info < (3, 11):
    print("Aplikacja wymaga Pythona 3.11 lub nowszego, a działa na %s." % (sys.version.split()[0],))
    print("Zmień wersję w panelu (Aplikacje Python) i powtórz instalację zależności.")
    raise SystemExit(1)

from app.cli import main  # noqa: E402

if len(sys.argv) < 2:
    print(__doc__)
    raise SystemExit(0)

main(sys.argv[1:])
