from __future__ import annotations

from app.configuration.models import ApplicationSettings
from app.configuration.sources.environment_source import EnvironmentSource
from app.configuration.sources.ini_config_source import IniConfigSource
from app.configuration.value_parser import ConfigValueParser
from app.core.config_error import ConfigError


class ApplicationSettingsReader:
    VALID_ENVIRONMENTS = frozenset({"development", "staging", "production"})

    def __init__(self, config: IniConfigSource, environment: EnvironmentSource) -> None:
        self._config = config
        self._environment = environment

    def read(self) -> ApplicationSettings:
        section = self._config.section("app")
        environment = self._environment.get("APP_ENV").lower()
        if environment not in self.VALID_ENVIRONMENTS:
            raise ConfigError("APP_ENV must be one of: development, staging, production.")
        return ApplicationSettings(
            name=ConfigValueParser.required(section, "name"),
            version=ConfigValueParser.required(section, "version"),
            environment=environment,
            api_prefix=ConfigValueParser.required(section, "api_prefix"),
        )
