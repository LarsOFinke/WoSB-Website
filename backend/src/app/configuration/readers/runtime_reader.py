from __future__ import annotations

from pathlib import Path

from app.configuration.models import SeedSettings, StorageSettings, UploadLimitSettings
from app.configuration.sources.environment_source import EnvironmentSource
from app.configuration.sources.ini_config_source import IniConfigSource
from app.configuration.value_parser import ConfigValueParser
from app.core.config_error import ConfigError
from app.core.runtime_paths import RuntimePathResolver


class RuntimeSettingsReader:
    WEAK_PASSWORDS = frozenset(
        {
            "admin",
            "admin123",
            "password",
            "changeme",
            "change_me",
            "CHANGE_ME_USE_A_LONG_RANDOM_PASSWORD",
        }
    )

    def __init__(
        self,
        config: IniConfigSource,
        environment: EnvironmentSource,
        backend_root: Path,
    ) -> None:
        self._config = config
        self._environment = environment
        self._paths = RuntimePathResolver(backend_root)
        self._backend_root = backend_root

    def read_storage(self) -> StorageSettings:
        upload_dir = self._paths.resolve(
            self._environment.get("UPLOAD_DIR"), setting_name="UPLOAD_DIR"
        )
        control_raw = self._environment.get(
            "CONTROL_DIR",
            required=False,
            default=str(self._backend_root / "storage" / "control"),
        )
        control_dir = self._paths.resolve(control_raw, setting_name="CONTROL_DIR")
        return StorageSettings(upload_dir=str(upload_dir), control_dir=str(control_dir))

    def read_seed(self) -> SeedSettings:
        auto_seed = ConfigValueParser.parse_boolean(
            self._environment.get("AUTO_SEED"), name="AUTO_SEED"
        )
        username = self._environment.get("SEED_ADMIN_USERNAME", required=auto_seed)
        password = self._environment.get("SEED_ADMIN_PASSWORD", required=auto_seed)
        display_name = self._environment.get("SEED_ADMIN_DISPLAY_NAME", required=auto_seed)
        if auto_seed and self._weak_password(password):
            raise ConfigError(
                "SEED_ADMIN_PASSWORD must be changed to a strong non-default value before startup."
            )
        return SeedSettings(
            auto_seed=auto_seed,
            admin_username=username,
            admin_password=password,
            admin_display_name=display_name,
        )

    def read_upload_limits(self) -> UploadLimitSettings:
        section = self._config.section("upload_limits")
        return UploadLimitSettings(
            image_mb=ConfigValueParser.integer(section, "image_mb"),
            document_mb=ConfigValueParser.integer(section, "document_mb"),
            video_mb=ConfigValueParser.integer(section, "video_mb"),
        )

    def read_cors_origins(self) -> tuple[str, ...]:
        return ConfigValueParser.csv(
            self._environment.get("CORS_ORIGINS"), name="CORS_ORIGINS"
        )

    @classmethod
    def _weak_password(cls, password: str) -> bool:
        return password in cls.WEAK_PASSWORDS or len(password) < 12
