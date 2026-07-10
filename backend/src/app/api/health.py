from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.session import engine

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.environment,
        "database": settings.database_backend,
    }


@router.get("/health/ready")
def readiness_check() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            if settings.database_schema_mode == "migrate":
                connection.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database is not ready.") from exc
    return {
        "status": "ready",
        "database": settings.database_backend,
    }
