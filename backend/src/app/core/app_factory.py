from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from urllib.parse import urlsplit

from app.api.router import router as api_router
from app.configuration.models import Settings
from app.core.config import settings
from app.core.errors import AppError, app_error_handler, http_error_handler
from app.core.logging import LoggingConfigurator
from app.core.maintenance import (
    maintenance_loop,
    run_maintenance_once,
    webhook_delivery_recovery_loop,
)
from app.core.middleware import CsrfOriginMiddleware, IpBlockMiddleware, RequestLoggingMiddleware
from app.db.init_db import create_and_seed, create_tables, verify_database_ready
from app.modules.files.routes.content import legacy_router as legacy_upload_router
from app.modules.registry import register_all_models


class ApplicationFactory:
    DESCRIPTION = (
        "Royal Blackwater Fleet API for newcomer guides, shared builds, forum Q&A, "
        "scheduled events and fleet operations."
    )

    def __init__(self, application_settings: Settings) -> None:
        self._settings = application_settings

    def create(self) -> FastAPI:
        LoggingConfigurator(self._settings).configure()
        app = FastAPI(
            title=self._settings.app_name,
            version=self._settings.app_version,
            description=self.DESCRIPTION,
            lifespan=self._lifespan,
            docs_url=None if self._settings.is_production else "/docs",
            redoc_url=None if self._settings.is_production else "/redoc",
            openapi_url=None if self._settings.is_production else "/openapi.json",
        )
        self._configure_errors(app)
        self._configure_middleware(app)
        self._configure_routes(app)
        return app

    @asynccontextmanager
    async def _lifespan(self, _: FastAPI) -> AsyncIterator[None]:
        register_all_models()
        if self._settings.manages_schema_at_startup:
            if self._settings.auto_seed:
                create_and_seed()
            else:
                create_tables()
        else:
            verify_database_ready()
        run_maintenance_once()
        maintenance_task = asyncio.create_task(maintenance_loop())
        webhook_recovery_task = (
            asyncio.create_task(webhook_delivery_recovery_loop())
            if self._settings.is_production
            else None
        )
        try:
            yield
        finally:
            tasks = [maintenance_task]
            if webhook_recovery_task is not None:
                tasks.append(webhook_recovery_task)
            for task in tasks:
                task.cancel()
            for task in tasks:
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    @staticmethod
    def _configure_errors(app: FastAPI) -> None:
        app.add_exception_handler(AppError, app_error_handler)
        app.add_exception_handler(HTTPException, http_error_handler)

    def _configure_middleware(self, app: FastAPI) -> None:
        allowed_hosts = {"testserver", "localhost", "127.0.0.1"}
        for origin in self._settings.cors_origins:
            hostname = urlsplit(origin).hostname
            if hostname:
                allowed_hosts.add(hostname)
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=sorted(allowed_hosts),
        )
        app.add_middleware(IpBlockMiddleware)
        app.add_middleware(RequestLoggingMiddleware)
        app.add_middleware(
            CsrfOriginMiddleware,
            allowed_origins=self._settings.cors_origins,
        )
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(self._settings.cors_origins),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _configure_routes(self, app: FastAPI) -> None:
        app.include_router(legacy_upload_router)
        app.include_router(api_router, prefix=self._settings.api_prefix)


def create_app() -> FastAPI:
    return ApplicationFactory(settings).create()


__all__ = ["ApplicationFactory", "create_app"]
