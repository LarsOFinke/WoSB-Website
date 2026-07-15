from __future__ import annotations

from pathlib import Path

from app.configuration.models import DatabaseSettings
from app.configuration.sources.environment_source import EnvironmentSource
from app.core.config_error import ConfigError
from app.core.database_mode import DatabaseSchemaMode
from app.core.runtime_paths import DatabaseUrlNormalizer


class DatabaseSettingsReader:
    def __init__(self, environment: EnvironmentSource, backend_root: Path) -> None:
        self._environment = environment
        self._backend_root = backend_root

    def read(self, *, application_environment: str) -> DatabaseSettings:
        schema_mode = self._environment.get("DB_SCHEMA_MODE").lower()
        valid_modes = {mode.value for mode in DatabaseSchemaMode}
        if schema_mode not in valid_modes:
            raise ConfigError(
                f"DB_SCHEMA_MODE must be one of: {', '.join(sorted(valid_modes))}."
            )
        if application_environment == "production" and schema_mode != DatabaseSchemaMode.MIGRATE:
            raise ConfigError(
                "APP_ENV=production requires DB_SCHEMA_MODE=migrate so Alembic owns the schema."
            )

        url = DatabaseUrlNormalizer(self._backend_root).normalize(
            self._environment.get("DATABASE_URL")
        )
        settings = DatabaseSettings(url=url, schema_mode=schema_mode)
        if application_environment == "production" and settings.backend != "postgresql":
            raise ConfigError(
                "APP_ENV=production requires a PostgreSQL DATABASE_URL. "
                "Use SQLite only for development or tests."
            )
        return settings
