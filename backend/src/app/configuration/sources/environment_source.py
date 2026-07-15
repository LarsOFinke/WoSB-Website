from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from app.core.config_error import ConfigError


class EnvironmentSource:
    """Loads the mandatory dotenv file and overlays process environment values."""

    def __init__(
        self,
        path: Path,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        self.path = path
        self._environ = environ if environ is not None else os.environ
        self._file_values = self._read_required_file(path)

    def get(self, name: str, *, required: bool = True, default: str = "") -> str:
        raw = self._environ.get(name, self._file_values.get(name, default))
        value = str(raw).strip() if raw is not None else ""
        if required and not value:
            raise ConfigError(f"Missing required environment value: {name}.")
        return value

    @classmethod
    def _read_required_file(cls, path: Path) -> dict[str, str]:
        if not path.exists():
            raise ConfigError(
                f"Missing required env file: {path}. "
                "Copy backend/.env.example to backend/.env or set RBF_ENV_FILE."
            )
        if not path.is_file():
            raise ConfigError(f"Env path is not a file: {path}")

        values: dict[str, str] = {}
        for line_number, raw_line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            if "=" not in line:
                raise ConfigError(
                    f"Invalid env line in {path}:{line_number}; expected KEY=value."
                )
            key, raw_value = line.split("=", 1)
            key = key.strip()
            if not cls._valid_key(key):
                raise ConfigError(f"Invalid env key in {path}:{line_number}: {key!r}.")
            values[key] = cls._strip_quotes(raw_value)
        return values

    @staticmethod
    def _valid_key(key: str) -> bool:
        return bool(key) and not key[0].isdigit() and key.replace("_", "").isalnum()

    @staticmethod
    def _strip_quotes(value: str) -> str:
        normalized = value.strip()
        if (
            len(normalized) >= 2
            and normalized[0] == normalized[-1]
            and normalized[0] in {'"', "'"}
        ):
            return normalized[1:-1]
        return normalized
