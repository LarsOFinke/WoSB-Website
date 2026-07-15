from __future__ import annotations

from app.configuration.models import SessionSettings
from app.configuration.sources.environment_source import EnvironmentSource
from app.configuration.sources.ini_config_source import IniConfigSource
from app.configuration.value_parser import ConfigValueParser
from app.core.config_error import ConfigError


class SessionSettingsReader:
    VALID_SAMESITE_VALUES = frozenset({"lax", "strict", "none"})

    def __init__(self, config: IniConfigSource, environment: EnvironmentSource) -> None:
        self._config = config
        self._environment = environment

    def read(self, *, application_environment: str) -> SessionSettings:
        section = self._config.section("session")
        samesite = ConfigValueParser.required(section, "cookie_samesite").lower()
        if samesite not in self.VALID_SAMESITE_VALUES:
            raise ConfigError("[session].cookie_samesite must be lax, strict or none.")
        secure = ConfigValueParser.parse_boolean(
            self._environment.get("SESSION_COOKIE_SECURE"),
            name="SESSION_COOKIE_SECURE",
        )
        if application_environment == "production" and not secure:
            raise ConfigError("SESSION_COOKIE_SECURE must be true when APP_ENV=production.")
        return SessionSettings(
            cookie_name=ConfigValueParser.required(section, "cookie_name"),
            cookie_secure=secure,
            cookie_samesite=samesite,
            ttl_hours=ConfigValueParser.integer(section, "ttl_hours"),
        )
