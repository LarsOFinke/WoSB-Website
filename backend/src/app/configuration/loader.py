from __future__ import annotations

from pathlib import Path
from collections.abc import Mapping

from app.configuration.models import Settings
from app.configuration.paths import ConfigurationPaths
from app.configuration.readers.application_reader import ApplicationSettingsReader
from app.configuration.readers.database_reader import DatabaseSettingsReader
from app.configuration.readers.logging_reader import LoggingSettingsReader
from app.configuration.readers.runtime_reader import RuntimeSettingsReader
from app.configuration.readers.session_reader import SessionSettingsReader
from app.configuration.sources.environment_source import EnvironmentSource
from app.configuration.sources.ini_config_source import IniConfigSource


class SettingsLoader:
    """Composition root for all configuration sources and readers."""

    def __init__(self, paths: ConfigurationPaths, environ: Mapping[str, str] | None = None) -> None:
        self._paths = paths
        self._environment = EnvironmentSource(paths.env_path, environ=environ)
        self._config = IniConfigSource(paths.config_path)

    @classmethod
    def for_backend(
        cls,
        backend_root: Path,
        environ: Mapping[str, str] | None = None,
    ) -> "SettingsLoader":
        return cls(ConfigurationPaths.resolve(backend_root, environ), environ=environ)

    def load(self) -> Settings:
        application = ApplicationSettingsReader(self._config, self._environment).read()
        runtime_reader = RuntimeSettingsReader(
            self._config,
            self._environment,
            self._paths.backend_root,
        )
        return Settings(
            application=application,
            database=DatabaseSettingsReader(
                self._environment,
                self._paths.backend_root,
            ).read(application_environment=application.environment),
            storage=runtime_reader.read_storage(),
            logging=LoggingSettingsReader(self._config).read(),
            session=SessionSettingsReader(self._config, self._environment).read(
                application_environment=application.environment
            ),
            seed=runtime_reader.read_seed(),
            upload_limits=runtime_reader.read_upload_limits(),
            cors_origins=runtime_reader.read_cors_origins(),
        )
