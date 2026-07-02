from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, auth, builds, groups, health, profile, ships
from app.core.config import settings
from app.db.init_db import init_db
from app.db.session import SessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    with SessionLocal() as db:
        init_db(db)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.4.2",
        description="MVP-Backend für die WoSB Gruppenmanagement-Webseite mit Backend-Auth, Rollen und SQLAlchemy.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix=settings.api_v1_prefix)
    app.include_router(auth.router, prefix=settings.api_v1_prefix)
    app.include_router(ships.router, prefix=settings.api_v1_prefix)
    app.include_router(groups.router, prefix=settings.api_v1_prefix)
    app.include_router(profile.router, prefix=settings.api_v1_prefix)
    app.include_router(builds.router, prefix=settings.api_v1_prefix)
    app.include_router(admin.router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
