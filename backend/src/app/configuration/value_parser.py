from __future__ import annotations

from configparser import SectionProxy

from app.core.config_error import ConfigError


class ConfigValueParser:
    TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
    FALSE_VALUES = frozenset({"0", "false", "no", "off"})

    @classmethod
    def required(cls, section: SectionProxy, key: str) -> str:
        value = section.get(key, "").strip()
        if not value:
            raise ConfigError(f"Config value [{section.name}].{key} must not be empty.")
        return value

    @classmethod
    def integer(cls, section: SectionProxy, key: str) -> int:
        raw = cls.required(section, key)
        try:
            return int(raw)
        except ValueError as exc:
            raise ConfigError(
                f"Config value [{section.name}].{key} must be an integer."
            ) from exc

    @classmethod
    def boolean(cls, section: SectionProxy, key: str) -> bool:
        return cls.parse_boolean(cls.required(section, key), name=f"[{section.name}].{key}")

    @classmethod
    def parse_boolean(cls, value: str, *, name: str) -> bool:
        normalized = value.strip().lower()
        if normalized in cls.TRUE_VALUES:
            return True
        if normalized in cls.FALSE_VALUES:
            return False
        raise ConfigError(f"{name} must be a boolean value, got {value!r}.")

    @staticmethod
    def csv(value: str, *, name: str) -> tuple[str, ...]:
        items = tuple(item.strip() for item in value.split(",") if item.strip())
        if not items:
            raise ConfigError(f"{name} must contain at least one value.")
        return items
