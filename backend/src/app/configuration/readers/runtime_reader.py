from __future__ import annotations

import base64
import binascii
from pathlib import Path

from app.configuration.models import (
    LegalNoticeSettings,
    MaintenanceSettings,
    SecuritySettings,
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
            raise ConfigError(f"Config value [{section.name}].{key} must be an integer.") from exc

    @classmethod
    def _positive_integer_or_default(cls, section, key: str, default: int) -> int:
        value = cls._integer_or_default(section, key, default)
        if value < 1:
            raise ConfigError(f"Config value [{section.name}].{key} must be greater than zero.")
        return value

    def _optional_section(self, name: str):
        target = name.casefold()
        return next(
            (
                section
                for key, section in self._config.sections().items()
                if key.casefold() == target
            ),
            None,
        )

    def read_upload_limits(self) -> UploadLimitSettings:
        section = self._config.section("upload_limits")
        return UploadLimitSettings(
            image_mb=ConfigValueParser.integer(section, "image_mb"),
            document_mb=ConfigValueParser.integer(section, "document_mb"),
            video_mb=ConfigValueParser.integer(section, "video_mb"),
            per_user_total_mb=self._positive_integer_or_default(section, "per_user_total_mb", 2048),
            global_total_mb=self._positive_integer_or_default(section, "global_total_mb", 20480),
            minimum_free_mb=self._positive_integer_or_default(section, "minimum_free_mb", 1024),
        )

    def read_maintenance(self) -> MaintenanceSettings:
        section = self._optional_section("maintenance")
        if section is None:
            return MaintenanceSettings(
                security_event_retention_days=7,
                inactive_ip_block_retention_days=90,
                audit_log_retention_days=365,
                webhook_delivery_retention_days=30,
                cookie_consent_retention_days=400,
                resolved_privacy_request_retention_days=400,
                pending_registration_retention_days=30,
                reviewed_registration_retention_days=90,
                interval_hours=24,
            )
        return MaintenanceSettings(
            security_event_retention_days=self._positive_integer_or_default(
                section, "security_event_retention_days", 7
            ),
            inactive_ip_block_retention_days=self._positive_integer_or_default(
                section, "inactive_ip_block_retention_days", 90
            ),
            audit_log_retention_days=self._positive_integer_or_default(
                section, "audit_log_retention_days", 365
            ),
            webhook_delivery_retention_days=self._positive_integer_or_default(
                section, "webhook_delivery_retention_days", 30
            ),
            cookie_consent_retention_days=self._positive_integer_or_default(
                section, "cookie_consent_retention_days", 400
            ),
            resolved_privacy_request_retention_days=self._positive_integer_or_default(
                section, "resolved_privacy_request_retention_days", 400
            ),
            pending_registration_retention_days=self._positive_integer_or_default(
                section, "pending_registration_retention_days", 30
            ),
            reviewed_registration_retention_days=self._positive_integer_or_default(
                section, "reviewed_registration_retention_days", 90
            ),
            interval_hours=self._positive_integer_or_default(section, "interval_hours", 24),
        )

    def read_legal_notice(self) -> LegalNoticeSettings:
        get = self._environment.get
        legal_notice = LegalNoticeSettings(
            published=ConfigValueParser.parse_boolean(
                get("LEGAL_NOTICE_PUBLISHED", required=False, default="false"),
                name="LEGAL_NOTICE_PUBLISHED",
            ),
            provider_name=get("LEGAL_NOTICE_PROVIDER_NAME", required=False, default=""),
            legal_form=get("LEGAL_NOTICE_LEGAL_FORM", required=False, default=""),
            represented_by=get("LEGAL_NOTICE_REPRESENTED_BY", required=False, default=""),
            street=get("LEGAL_NOTICE_STREET", required=False, default=""),
            postal_code=get("LEGAL_NOTICE_POSTAL_CODE", required=False, default=""),
            city=get("LEGAL_NOTICE_CITY", required=False, default=""),
            country=get("LEGAL_NOTICE_COUNTRY", required=False, default="Deutschland"),
            email=get("LEGAL_NOTICE_EMAIL", required=False, default=""),
            phone=get("LEGAL_NOTICE_PHONE", required=False, default=""),
            register_name=get("LEGAL_NOTICE_REGISTER_NAME", required=False, default=""),
            register_court=get("LEGAL_NOTICE_REGISTER_COURT", required=False, default=""),
            register_number=get("LEGAL_NOTICE_REGISTER_NUMBER", required=False, default=""),
            vat_id=get("LEGAL_NOTICE_VAT_ID", required=False, default=""),
            business_id=get("LEGAL_NOTICE_BUSINESS_ID", required=False, default=""),
            supervisory_authority=get(
                "LEGAL_NOTICE_SUPERVISORY_AUTHORITY", required=False, default=""
            ),
            editorial_responsible_name=get(
                "LEGAL_NOTICE_EDITORIAL_RESPONSIBLE_NAME", required=False, default=""
            ),
            editorial_responsible_street=get(
                "LEGAL_NOTICE_EDITORIAL_RESPONSIBLE_STREET", required=False, default=""
            ),
            editorial_responsible_postal_code=get(
                "LEGAL_NOTICE_EDITORIAL_RESPONSIBLE_POSTAL_CODE", required=False, default=""
            ),
            editorial_responsible_city=get(
                "LEGAL_NOTICE_EDITORIAL_RESPONSIBLE_CITY", required=False, default=""
            ),
            editorial_responsible_country=get(
                "LEGAL_NOTICE_EDITORIAL_RESPONSIBLE_COUNTRY",
                required=False,
                default="Deutschland",
            ),
            dispute_resolution_text=get(
                "LEGAL_NOTICE_DISPUTE_RESOLUTION_TEXT", required=False, default=""
            ),
            additional_information=get(
                "LEGAL_NOTICE_ADDITIONAL_INFORMATION", required=False, default=""
            ),
        )
        if legal_notice.email and (
            "@" not in legal_notice.email
            or legal_notice.email.startswith("@")
            or legal_notice.email.endswith("@")
        ):
            raise ConfigError("LEGAL_NOTICE_EMAIL must be a valid contact email address.")
        if legal_notice.published:
            required = {
                "LEGAL_NOTICE_PROVIDER_NAME": legal_notice.provider_name,
                "LEGAL_NOTICE_STREET": legal_notice.street,
                "LEGAL_NOTICE_POSTAL_CODE": legal_notice.postal_code,
                "LEGAL_NOTICE_CITY": legal_notice.city,
                "LEGAL_NOTICE_COUNTRY": legal_notice.country,
                "LEGAL_NOTICE_EMAIL": legal_notice.email,
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                raise ConfigError(
                    "A published legal notice requires complete provider details. "
                    f"Missing environment values: {', '.join(missing)}."
                )
        editorial = (
            legal_notice.editorial_responsible_name,
            legal_notice.editorial_responsible_street,
            legal_notice.editorial_responsible_postal_code,
            legal_notice.editorial_responsible_city,
        )
        if any(editorial) and not all(editorial):
            raise ConfigError(
                "Editorial legal-notice environment values require name and a complete address."
            )
        return legal_notice

    def read_security(self) -> SecuritySettings:
        raw = self._environment.get("WEBHOOK_ENCRYPTION_KEYS", required=False, default="")
        if not raw:
            return SecuritySettings(webhook_encryption_keys=())
        keys = ConfigValueParser.csv(raw, name="WEBHOOK_ENCRYPTION_KEYS")
        for key in keys:
            try:
                decoded = base64.b64decode(key.encode("ascii"), altchars=b"-_", validate=True)
            except (UnicodeEncodeError, binascii.Error, ValueError) as exc:
                raise ConfigError(
                    "WEBHOOK_ENCRYPTION_KEYS must contain URL-safe Base64 Fernet keys."
                ) from exc
            if len(decoded) != 32:
                raise ConfigError(
                    "Each WEBHOOK_ENCRYPTION_KEYS entry must decode to exactly 32 bytes."
                )
        return SecuritySettings(webhook_encryption_keys=keys)

    def read_cors_origins(self) -> tuple[str, ...]:
        return ConfigValueParser.csv(self._environment.get("CORS_ORIGINS"), name="CORS_ORIGINS")

    @classmethod
    def _weak_password(cls, password: str) -> bool:
        return password in cls.WEAK_PASSWORDS or len(password) < 12
