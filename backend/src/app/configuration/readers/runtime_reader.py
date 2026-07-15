from __future__ import annotations

from pathlib import Path

from app.configuration.models import (
    MaintenanceSettings,
    SeedSettings,
    StorageSettings,
    UploadLimitSettings,
)
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
        legacy_control = self._environment.get(
            "CONTROL_DIR",
            required=False,
            default=str(self._backend_root / "storage" / "control"),
        )
        request_raw = self._environment.get(
            "CONTROL_REQUEST_DIR", required=False, default=legacy_control
        )
        status_raw = self._environment.get(
            "CONTROL_STATUS_DIR", required=False, default=legacy_control
        )
        request_dir = self._paths.resolve(request_raw, setting_name="CONTROL_REQUEST_DIR")
        status_dir = self._paths.resolve(status_raw, setting_name="CONTROL_STATUS_DIR")
        return StorageSettings(
            upload_dir=str(upload_dir),
            control_request_dir=str(request_dir),
            control_status_dir=str(status_dir),
        )

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

    @staticmethod
    def _integer_or_default(section, key: str, default: int) -> int:
        raw = section.get(key, "").strip()
        if not raw:
            return default
        try:
            return int(raw)
        except ValueError as exc:
            raise ConfigError(
                f"Config value [{section.name}].{key} must be an integer."
            ) from exc

    def _optional_section(self, name: str):
        target = name.casefold()
        return next(
            (section for key, section in self._config.sections().items() if key.casefold() == target),
            None,
        )

    def read_upload_limits(self) -> UploadLimitSettings:
        section = self._config.section("upload_limits")
        return UploadLimitSettings(
            image_mb=ConfigValueParser.integer(section, "image_mb"),
            document_mb=ConfigValueParser.integer(section, "document_mb"),
            video_mb=ConfigValueParser.integer(section, "video_mb"),
            per_user_total_mb=self._integer_or_default(section, "per_user_total_mb", 2048),
            global_total_mb=self._integer_or_default(section, "global_total_mb", 20480),
            minimum_free_mb=self._integer_or_default(section, "minimum_free_mb", 1024),
        )

    def read_maintenance(self) -> MaintenanceSettings:
        section = self._optional_section("maintenance")
        if section is None:
            return MaintenanceSettings(
                app_log_retention_days=30,
                audit_log_retention_days=365,
                interval_hours=24,
            )
        return MaintenanceSettings(
            app_log_retention_days=self._integer_or_default(
                section, "app_log_retention_days", 30
            ),
            audit_log_retention_days=self._integer_or_default(
                section, "audit_log_retention_days", 365
            ),
            interval_hours=self._integer_or_default(section, "interval_hours", 24),
        )

    def read_cors_origins(self) -> tuple[str, ...]:
        return ConfigValueParser.csv(
            self._environment.get("CORS_ORIGINS"), name="CORS_ORIGINS"
        )

    @classmethod
    def _weak_password(cls, password: str) -> bool:
        return password in cls.WEAK_PASSWORDS or len(password) < 12
