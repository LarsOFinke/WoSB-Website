from __future__ import annotations

import logging.config
from typing import Any

from app.configuration.models import Settings
from app.core.config import settings
from app.core.database_log_handler import DatabaseLogHandler
from app.core.json_formatter import JsonFormatter


class LoggingConfigurator:
    def __init__(self, application_settings: Settings) -> None:
        self._settings = application_settings

    def configure(self) -> None:
        logging.config.dictConfig(self.build_config())

    def build_config(self) -> dict[str, Any]:
        formatter_name = "json" if self._settings.log_format == "json" else "default"
        handlers = self._build_handlers(formatter_name)
        app_handlers = self._enabled_app_handlers()
        root_handlers = ["console"] if self._settings.console_logging_enabled else ["null"]
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                },
                "json": {"()": "app.core.json_formatter.JsonFormatter"},
            },
            "handlers": handlers,
            "root": {"level": self._settings.log_level, "handlers": root_handlers},
            "loggers": {
                "app": {
                    "level": self._settings.log_level,
                    "handlers": app_handlers,
                    "propagate": False,
                },
                "uvicorn.access": {"level": "WARNING"},
                "sqlalchemy.engine": {"level": self._settings.sql_log_level},
            },
        }

    def _build_handlers(self, formatter_name: str) -> dict[str, dict[str, Any]]:
        return {
            "console": {
                "class": "logging.StreamHandler",
                "level": self._settings.log_level,
                "formatter": formatter_name,
            },
            "database": {
                "()": "app.core.database_log_handler.DatabaseLogHandler",
                "level": self._settings.db_log_level,
                "formatter": "default",
            },
            "null": {"class": "logging.NullHandler"},
        }

    def _enabled_app_handlers(self) -> list[str]:
        handlers: list[str] = []
        if self._settings.console_logging_enabled:
            handlers.append("console")
        if self._settings.db_logging_enabled:
            handlers.append("database")
        return handlers or ["null"]


def configure_logging() -> None:
    LoggingConfigurator(settings).configure()


__all__ = [
    "DatabaseLogHandler",
    "JsonFormatter",
    "LoggingConfigurator",
    "configure_logging",
]
