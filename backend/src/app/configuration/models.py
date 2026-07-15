from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ApplicationSettings:
    name: str
    version: str
    environment: str
    api_prefix: str

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@dataclass(frozen=True, slots=True)
class DatabaseSettings:
    url: str
    schema_mode: str

    @property
    def backend(self) -> str:
        return self.url.split(":", 1)[0].split("+", 1)[0]

    @property
    def manages_schema_at_startup(self) -> bool:
        return self.schema_mode == "create"


@dataclass(frozen=True, slots=True)
class StorageSettings:
    upload_dir: str
    control_request_dir: str
    control_status_dir: str


@dataclass(frozen=True, slots=True)
class LoggingSettings:
    level: str
    format: str
    sql_level: str
    database_enabled: bool
    database_level: str
    console_enabled: bool


@dataclass(frozen=True, slots=True)
class SessionSettings:
    cookie_name: str
    cookie_secure: bool
    cookie_samesite: str
    ttl_hours: int


@dataclass(frozen=True, slots=True)
class SeedSettings:
    auto_seed: bool
    admin_username: str
    admin_password: str
    admin_display_name: str


@dataclass(frozen=True, slots=True)
class UploadLimitSettings:
    image_mb: int
    document_mb: int
    video_mb: int
    per_user_total_mb: int
    global_total_mb: int
    minimum_free_mb: int


@dataclass(frozen=True, slots=True)
class MaintenanceSettings:
    app_log_retention_days: int
    audit_log_retention_days: int
    interval_hours: int


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable aggregate configuration with a compatibility property surface."""

    application: ApplicationSettings
    database: DatabaseSettings
    storage: StorageSettings
    logging: LoggingSettings
    session: SessionSettings
    seed: SeedSettings
    upload_limits: UploadLimitSettings
    maintenance: MaintenanceSettings
    cors_origins: tuple[str, ...]

    @property
    def app_name(self) -> str:
        return self.application.name

    @property
    def app_version(self) -> str:
        return self.application.version

    @property
    def environment(self) -> str:
        return self.application.environment

    @property
    def api_prefix(self) -> str:
        return self.application.api_prefix

    @property
    def is_production(self) -> bool:
        return self.application.is_production

    @property
    def database_url(self) -> str:
        return self.database.url

    @property
    def database_schema_mode(self) -> str:
        return self.database.schema_mode

    @property
    def database_backend(self) -> str:
        return self.database.backend

    @property
    def manages_schema_at_startup(self) -> bool:
        return self.database.manages_schema_at_startup

    @property
    def upload_dir(self) -> str:
        return self.storage.upload_dir

    @property
    def control_request_dir(self) -> str:
        return self.storage.control_request_dir

    @property
    def control_status_dir(self) -> str:
        return self.storage.control_status_dir

    @property
    def control_dir(self) -> str:
        """Legacy alias used by local tests where request and status share a directory."""
        return self.storage.control_request_dir

    @property
    def auto_seed(self) -> bool:
        return self.seed.auto_seed

    @property
    def log_level(self) -> str:
        return self.logging.level

    @property
    def log_format(self) -> str:
        return self.logging.format

    @property
    def sql_log_level(self) -> str:
        return self.logging.sql_level

    @property
    def db_logging_enabled(self) -> bool:
        return self.logging.database_enabled

    @property
    def db_log_level(self) -> str:
        return self.logging.database_level

    @property
    def console_logging_enabled(self) -> bool:
        return self.logging.console_enabled

    @property
    def session_cookie_name(self) -> str:
        return self.session.cookie_name

    @property
    def session_cookie_secure(self) -> bool:
        return self.session.cookie_secure

    @property
    def session_cookie_samesite(self) -> str:
        return self.session.cookie_samesite

    @property
    def session_ttl_hours(self) -> int:
        return self.session.ttl_hours

    @property
    def seed_admin_username(self) -> str:
        return self.seed.admin_username

    @property
    def seed_admin_password(self) -> str:
        return self.seed.admin_password

    @property
    def seed_admin_display_name(self) -> str:
        return self.seed.admin_display_name

    @property
    def upload_image_limit_mb(self) -> int:
        return self.upload_limits.image_mb

    @property
    def upload_document_limit_mb(self) -> int:
        return self.upload_limits.document_mb

    @property
    def upload_video_limit_mb(self) -> int:
        return self.upload_limits.video_mb

    @property
    def upload_per_user_total_mb(self) -> int:
        return self.upload_limits.per_user_total_mb

    @property
    def upload_global_total_mb(self) -> int:
        return self.upload_limits.global_total_mb

    @property
    def upload_minimum_free_mb(self) -> int:
        return self.upload_limits.minimum_free_mb
