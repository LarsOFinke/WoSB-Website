from __future__ import annotations

from configparser import ConfigParser, SectionProxy
from pathlib import Path

from app.core.config_error import ConfigError


class IniConfigSource:
    """Provides case-insensitive sections from one file or a directory of .cfg files."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._parser = ConfigParser(interpolation=None)
        self._files = self._resolve_files(path)
        loaded = self._parser.read(self._files, encoding="utf-8")
        if len(loaded) != len(self._files):
            missing = sorted(set(map(str, self._files)) - set(loaded))
            raise ConfigError(f"Could not read configuration files: {', '.join(missing)}")

    @property
    def files(self) -> tuple[Path, ...]:
        return self._files

    def section(self, name: str) -> SectionProxy:
        resolved = self._resolve_section_name(name)
        if resolved is None:
            raise ConfigError(
                f"Missing required config section [{name}] in {self.path}."
            )
        return self._parser[resolved]

    def sections(self) -> dict[str, SectionProxy]:
        return {name: self._parser[name] for name in self._parser.sections()}

    @staticmethod
    def _resolve_files(path: Path) -> tuple[Path, ...]:
        if not path.exists():
            raise ConfigError(
                f"Missing required config path: {path}. "
                "Keep backend/config/*.cfg in the deployment or set RBF_CONFIG_DIR."
            )
        if path.is_file():
            if path.suffix.lower() != ".cfg":
                raise ConfigError(f"Config file must use the .cfg extension: {path}")
            return (path,)
        if not path.is_dir():
            raise ConfigError(f"Config path is neither a file nor directory: {path}")
        files = tuple(sorted(path.glob("*.cfg")))
        if not files:
            raise ConfigError(f"No .cfg files found in configuration directory: {path}")
        return files

    def _resolve_section_name(self, name: str) -> str | None:
        target = name.strip().lower()
        return next(
            (section for section in self._parser.sections() if section.strip().lower() == target),
            None,
        )
