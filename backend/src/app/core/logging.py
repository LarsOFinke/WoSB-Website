from __future__ import annotations

import logging.config
from typing import Any

from app.core.config import settings
from app.core.database_log_handler import DatabaseLogHandler
from app.core.json_formatter import JsonFormatter


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
            "()": "app.core.database_log_handler.DatabaseLogHandler",
            "level": settings.db_log_level,
            "formatter": "default",
        },
    }
    root_handlers = ["console"] if settings.console_logging_enabled else []
    app_handlers: list[str] = []
    if settings.console_logging_enabled:
        app_handlers.append("console")
    if settings.db_logging_enabled:
        app_handlers.append("database")
    if not app_handlers:
        app_handlers.append("null")
    if not root_handlers:
        root_handlers.append("null")

    handlers["null"] = {"class": "logging.NullHandler"}

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                },
                "json": {
                    "()": "app.core.json_formatter.JsonFormatter",
                },
            },
            "handlers": handlers,
            "root": {
                "level": settings.log_level,
                "handlers": root_handlers,
            },
            "loggers": {
                "app": {"level": settings.log_level, "handlers": app_handlers, "propagate": False},
                "uvicorn.access": {"level": "WARNING"},
                "sqlalchemy.engine": {"level": settings.sql_log_level},
            },
        }
    )


__all__ = ["configure_logging", "JsonFormatter", "DatabaseLogHandler"]
