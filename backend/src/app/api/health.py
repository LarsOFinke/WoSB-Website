from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.schema_health import DatabaseSchemaMismatchError, verify_alembic_heads
from app.db.session import engine

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def readiness_check() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            if settings.database_schema_mode == "migrate":
                verify_alembic_heads(connection)
    except (SQLAlchemyError, DatabaseSchemaMismatchError) as exc:
        raise HTTPException(status_code=503, detail="Database is not ready.") from exc
    return {"status": "ready"}
