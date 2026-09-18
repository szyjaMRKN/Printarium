"""Aplikacja FastAPI — ewidencja działalności nierejestrowanej."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import audit, auth, backups, costs, dashboard, documents, health, meta, products, reports
from app.api.routes import sales as sales_routes
from app.api.routes import settings as settings_routes
from app.api.routes import users
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging_config import configure_logging
from app.core.middleware import RequestSizeLimitMiddleware, SecurityHeadersMiddleware
from app.core.static import mount_frontend
from app.core.version import APP_NAME, APP_VERSION

logger = logging.getLogger("app")

AUTO_BACKUP_INTERVAL_SECONDS = 300


def bootstrap() -> None:
    """Migracje, dane startowe i konto administratora ze zmiennych środowiskowych.

    Wywoływane z `lifespan` (uvicorn) oraz z `passenger_wsgi.py` na hostingu
    współdzielonym, gdzie serwer WSGI nie uruchamia zdarzeń lifespan.
    """
    from app.db.seed import ensure_admin_from_env, seed_reference_data
    from app.db.session import session_scope
    from app.services.backup_service import run_migrations

    settings = get_settings()
    settings.ensure_directories()
    run_migrations()
    with session_scope() as session:
        seed_reference_data(session)
        user = ensure_admin_from_env(session)
        if user is not None:
            logger.info("Utworzono konto administratora '%s' na podstawie zmiennych środowiskowych.", user.login)


async def _auto_backup_loop() -> None:
    """Automatyczne kopie zapasowe o godzinie ustawionej w konfiguracji."""
    from app.db.session import session_scope
    from app.services import backup_service

    while True:
        try:
            await asyncio.sleep(AUTO_BACKUP_INTERVAL_SECONDS)
            with session_scope() as session:
                if backup_service.due_for_automatic_backup(session):
                    backup = backup_service.create_backup(session, automatic=True, note="harmonogram")
                    logger.info("Utworzono automatyczną kopię zapasową %s", backup.filename)
        except asyncio.CancelledError:  # pragma: no cover - zamknięcie aplikacji
            raise
        except Exception:  # pragma: no cover - błąd nie może zatrzymać aplikacji
            logger.exception("Automatyczna kopia zapasowa nie powiodła się.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.app_debug)
    bootstrap()
    task = asyncio.create_task(_auto_backup_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


def create_app() -> FastAPI:
    settings = get_settings()
    docs_url = "/api/docs" if settings.enable_docs else None
    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        description=(
            "REST API ewidencji działalności nierejestrowanej. "
            "Wszystkie kwoty są liczbami całkowitymi w groszach."
        ),
        docs_url=docs_url,
        redoc_url="/api/redoc" if settings.enable_docs else None,
        openapi_url="/api/openapi.json" if settings.enable_docs else None,
        lifespan=lifespan,
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware, max_bytes=settings.max_upload_bytes + 1024 * 1024)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    prefix = settings.api_prefix
    app.include_router(health.router)
    app.include_router(health.router, prefix=prefix)
    app.include_router(auth.router, prefix=prefix)
    app.include_router(users.router, prefix=prefix)
    app.include_router(meta.router, prefix=prefix)
    app.include_router(sales_routes.router, prefix=prefix)
    app.include_router(products.router, prefix=prefix)
    app.include_router(costs.router, prefix=prefix)
    app.include_router(documents.router, prefix=prefix)
    app.include_router(reports.router, prefix=prefix)
    app.include_router(dashboard.router, prefix=prefix)
    app.include_router(settings_routes.router, prefix=prefix)
    app.include_router(backups.router, prefix=prefix)
    app.include_router(audit.router, prefix=prefix)

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message, "code": exc.code})

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {
                "field": ".".join(str(part) for part in error.get("loc", [])[1:]),
                "message": error.get("msg", "Nieprawidłowa wartość."),
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={"detail": "Dane formularza są nieprawidłowe.", "code": "blad_walidacji", "errors": errors},
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        # Szczegóły trafiają do logu serwera, użytkownik dostaje ogólny komunikat.
        logger.exception("Nieobsłużony błąd przy %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Wystąpił nieoczekiwany błąd serwera.", "code": "blad_serwera"},
        )

    # Frontend serwujemy tylko wtedy, gdy wskazano jego katalog (hosting
    # współdzielony). Podpięcie musi być ostatnie — trasy API są wcześniej.
    frontend = settings.frontend_path
    if frontend is not None:
        mount_frontend(app, frontend, prefix)
        logger.info("Serwuję frontend z katalogu %s", frontend)

    return app


app = create_app()
