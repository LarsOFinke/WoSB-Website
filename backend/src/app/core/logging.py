from __future__ import annotations

import json
import logging
import logging.config
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings


class JsonFormatter(logging.Formatter):
    """Small JSON formatter for production-friendly logs without extra deps."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("request_id", "method", "path", "status_code", "duration_ms", "client"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class DatabaseLogHandler(logging.Handler):
    """Persist application logs for the admin dashboard.

    The handler is intentionally attached only to the ``app`` logger tree to
    avoid storing noisy dependency/SQL logs. Failures are swallowed because
    logging must never break request handling.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            from app.db.session import SessionLocal
            from app.models import AppLog

            with SessionLocal() as db:
                entry = AppLog(
                    created_at=datetime.fromtimestamp(record.created, tz=timezone.utc).replace(tzinfo=None),
                    level=record.levelname,
                    logger=record.name[:120],
                    message=record.getMessage(),
                    request_id=getattr(record, "request_id", None),
                    method=getattr(record, "method", None),
                    path=getattr(record, "path", None),
                    status_code=getattr(record, "status_code", None),
                    duration_ms=getattr(record, "duration_ms", None),
                    client=getattr(record, "client", None),
                    exception=self.formatException(record.exc_info) if record.exc_info else None,
                )
                db.add(entry)
                db.commit()
        except Exception:
            return


def configure_logging() -> None:
    """Configure application logging from environment-backed settings."""

    formatter_name = "json" if settings.log_format == "json" else "default"
    handlers: dict[str, dict[str, Any]] = {
        "console": {
            "class": "logging.StreamHandler",
            "level": settings.log_level,
            "formatter": formatter_name,
        },
        "database": {
            "()": "app.core.logging.DatabaseLogHandler",
            "level": settings.db_log_level,
            "formatter": "default",
        },
    }
    app_handlers = ["console"]
    if settings.db_logging_enabled:
        app_handlers.append("database")

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                },
                "json": {
                    "()": "app.core.logging.JsonFormatter",
                },
            },
            "handlers": handlers,
            "root": {
                "level": settings.log_level,
                "handlers": ["console"],
            },
            "loggers": {
                "app": {"level": settings.log_level, "handlers": app_handlers, "propagate": False},
                "uvicorn.access": {"level": "WARNING"},
                "sqlalchemy.engine": {"level": settings.sql_log_level},
            },
        }
    )
