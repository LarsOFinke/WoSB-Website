from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import router as api_router
from app.core.config import settings
from app.core.errors import AppError, app_error_handler, http_error_handler
from app.core.logging import configure_logging
from app.core.middleware import IpBlockMiddleware, RequestLoggingMiddleware
from app.db.init_db import create_and_seed, create_tables, verify_database_ready
from app.modules.registry import register_all_models


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    register_all_models()
    if settings.manages_schema_at_startup:
        if settings.auto_seed:
            create_and_seed()
        else:
            create_tables()
    else:
        verify_database_ready()
    yield


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Royal Blackwater Fleet API for newcomer guides, shared builds, forum Q&A, scheduled events and fleet operations.",
        lifespan=lifespan,
    )

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_middleware(IpBlockMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=upload_path), name="uploads")

    app.include_router(api_router, prefix=settings.api_prefix)
    return app
