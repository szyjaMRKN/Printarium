"""Serwowanie zbudowanego frontendu przez backend.

Wariant z Dockerem oddaje pliki statyczne Caddy'emu i ten moduł jest wtedy
nieużywany. Na hostingu współdzielonym (Passenger) nie ma osobnego serwera
statycznego dla aplikacji, więc powłokę SPA wystawia ten sam proces co API.

Trasy API rejestrowane są wcześniej niż to podpięcie, dlatego mają
pierwszeństwo; nieznany adres poza API dostaje `index.html` (routing po
stronie przeglądarki).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

INDEX_FILE = "index.html"

# Pliki z hashem w nazwie (katalog `assets/`) można cache'ować bez końca,
# bo każda zmiana treści zmienia nazwę pliku.
IMMUTABLE_PREFIXES = ("assets/",)

# Powłoka i service worker muszą być sprawdzane przy każdym wejściu,
# inaczej po aktualizacji przeglądarka trzymałaby starą wersję aplikacji.
NO_CACHE_FILES = (INDEX_FILE, "sw.js", "manifest.webmanifest")


class SPAStaticFiles(StaticFiles):
    """Pliki statyczne z awaryjnym `index.html` dla ścieżek aplikacji."""

    def __init__(self, *, directory: Path, api_prefix: str) -> None:
        super().__init__(directory=directory)
        self.api_prefix = api_prefix.strip("/")

    def _is_api_path(self, path: str) -> bool:
        if not self.api_prefix:
            return False
        return path == self.api_prefix or path.startswith(f"{self.api_prefix}/")

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            response = await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            # Nieistniejący zasób API to błąd 404, a nie adres wewnątrz SPA.
            if exc.status_code != 404 or self._is_api_path(path):
                raise
            response = await super().get_response(INDEX_FILE, scope)
            path = INDEX_FILE

        if response.status_code == 200:
            if path.startswith(IMMUTABLE_PREFIXES):
                response.headers.setdefault("Cache-Control", "public, max-age=31536000, immutable")
            elif path in NO_CACHE_FILES:
                response.headers["Cache-Control"] = "no-cache"
        return response


def mount_frontend(app: FastAPI, directory: Path, api_prefix: str) -> None:
    """Podpina zbudowany frontend pod korzeń aplikacji."""
    app.mount("/", SPAStaticFiles(directory=directory, api_prefix=api_prefix), name="frontend")
