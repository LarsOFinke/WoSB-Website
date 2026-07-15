from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Mapping


ENV_PATH_VARIABLES = (
    "RBF_ENV_FILE",
    "RBV_ENV_FILE",
    "BLACKWATER_ENV_FILE",
    "WOSB_ENV_FILE",
)
CONFIG_PATH_VARIABLES = (
    "RBF_CONFIG_DIR",
    "RBF_CONFIG_FILE",
    "RBV_CONFIG_FILE",
    "BLACKWATER_CONFIG_FILE",
    "WOSB_CONFIG_FILE",
)


@dataclass(frozen=True, slots=True)
class ConfigurationPaths:
    backend_root: Path
    env_path: Path
    config_path: Path

    @classmethod
    def resolve(
        cls,
        backend_root: Path,
        environ: Mapping[str, str] | None = None,
    ) -> "ConfigurationPaths":
        values = environ if environ is not None else os.environ
        return cls(
            backend_root=backend_root,
            env_path=_first_path(values, ENV_PATH_VARIABLES, backend_root / ".env"),
            config_path=_first_path(values, CONFIG_PATH_VARIABLES, backend_root / "config"),
        )


def _first_path(values: Mapping[str, str], names: tuple[str, ...], default: Path) -> Path:
    for name in names:
        raw = values.get(name)
        if raw and raw.strip():
            return Path(raw).expanduser()
    return default
