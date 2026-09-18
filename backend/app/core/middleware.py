"""Nagłówki bezpieczeństwa i ograniczenie rozmiaru żądania."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import Settings, get_settings

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=(), interest-cohort=()",
}

# API zwraca wyłącznie dane — całkowicie blokujemy wykonywanie skryptów.
API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"

# Polityka dla powłoki aplikacji, gdy frontend serwuje ten sam proces
# (hosting współdzielony). Odpowiednik nagłówka z deploy/Caddyfile:
# 'unsafe-inline' dla stylów jest potrzebny, bo biblioteka wykresów ustawia
# style bezpośrednio na elementach SVG.
APP_CSP = (
    "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
    "script-src 'self'; connect-src 'self'; font-src 'self'; object-src 'none'; "
    "base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
)


def _csp_for(request: Request, settings: Settings) -> str:
    """Restrykcyjna polityka dla API, łagodniejsza dla powłoki aplikacji."""
    if settings.frontend_dir is None:
        return API_CSP
    # Pod Passengerem aplikacja bywa podpięta w podkatalogu domeny — ścieżkę
    # trasy liczymy bez tego przedrostka (root_path).
    root_path = request.scope.get("root_path", "")
    path = request.url.path
    if root_path and path.startswith(root_path):
        path = path[len(root_path) :] or "/"
    prefix = settings.api_prefix.rstrip("/")
    if path == "/health" or path == prefix or path.startswith(f"{prefix}/"):
        return API_CSP
    return APP_CSP


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        settings = get_settings()
        if settings.is_production:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        response.headers.setdefault("Content-Security-Policy", _csp_for(request, settings))
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Twardy limit rozmiaru żądania (uploady mają dodatkowy limit w serwisie)."""

    def __init__(self, app, max_bytes: int) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > self.max_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Żądanie jest zbyt duże.", "code": "zbyt_duze_zadanie"},
                    )
            except ValueError:
                pass
        return await call_next(request)
