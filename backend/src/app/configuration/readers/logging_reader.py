from __future__ import annotations

from app.configuration.models import LoggingSettings
from app.configuration.sources.ini_config_source import IniConfigSource
from app.configuration.value_parser import ConfigValueParser
from app.core.config_error import ConfigError


class LoggingSettingsReader:
    VALID_FORMATS = frozenset({"plain", "json"})

    def __init__(self, config: IniConfigSource) -> None:
        self._config = config

    def read(self) -> LoggingSettings:
        section = self._config.section("logging")
        log_format = ConfigValueParser.required(section, "format").lower()
        if log_format not in self.VALID_FORMATS:
            raise ConfigError("[logging].format must be plain or json.")
        return LoggingSettings(
            level=ConfigValueParser.required(section, "level").upper(),
            format=log_format,
            sql_level=ConfigValueParser.required(section, "sql_level").upper(),
            database_enabled=ConfigValueParser.boolean(section, "db_enabled"),
            database_level=ConfigValueParser.required(section, "db_level").upper(),
            console_enabled=ConfigValueParser.boolean(section, "console_enabled"),
        )
