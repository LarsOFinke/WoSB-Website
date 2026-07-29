from __future__ import annotations

import logging.config
from typing import Any

from app.configuration.models import Settings
from app.core.config import settings
from app.core.database_log_handler import SecurityEventHandler
from app.core.json_formatter import JsonFormatter


class LoggingConfigurator:
    def __init__(self, application_settings: Settings) -> None:
        self._settings = application_settings

    def configure(self) -> None:
        logging.config.dictConfig(self.build_config())

    def build_config(self) -> dict[str, Any]:
        formatter_name = "json" if self._settings.log_format == "json" else "default"
        handlers = self._build_handlers(formatter_name)
        app_handlers = ["console"] if self._settings.console_logging_enabled else ["null"]
        security_handlers = ["security_database"] if self._settings.db_logging_enabled else ["null"]
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
                # Exact IPs are written only by this dedicated logger and only
                # into daily purpose-bound security-signal buckets. They never enter
                # console/container logs.
                "app.security": {
                    "level": self._settings.db_log_level,
                    "handlers": security_handlers,
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
            "security_database": {
                "()": "app.core.database_log_handler.SecurityEventHandler",
                "level": self._settings.db_log_level,
            },
            "null": {"class": "logging.NullHandler"},
        }


def configure_logging() -> None:
    LoggingConfigurator(settings).configure()


__all__ = [
    "SecurityEventHandler",
    "JsonFormatter",
    "LoggingConfigurator",
    "configure_logging",
]
