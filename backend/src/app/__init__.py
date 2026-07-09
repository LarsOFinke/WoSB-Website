from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.core.config import settings
from app.db.init_db import create_and_seed


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    create_and_seed()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Minimal Iron Crown Fleet Hub API with Build Manager and Fleet Announcements prototypes.",
        lifespan=lifespan,
    )

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
