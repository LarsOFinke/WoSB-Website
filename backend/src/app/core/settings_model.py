from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    environment: str
    api_prefix: str
    database_url: str
    database_schema_mode: str
    upload_dir: str
    auto_seed: bool

    log_level: str
    log_format: str
    sql_log_level: str
    db_logging_enabled: bool
    db_log_level: str
    console_logging_enabled: bool

    session_cookie_name: str
    session_cookie_secure: bool
    session_cookie_samesite: str
    session_ttl_hours: int

    seed_admin_username: str
    seed_admin_password: str
    seed_admin_display_name: str
    cors_origins: list[str]

    upload_image_limit_mb: int
    upload_document_limit_mb: int
    upload_video_limit_mb: int

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def database_backend(self) -> str:
        return self.database_url.split(":", 1)[0].split("+", 1)[0]

    @property
    def manages_schema_at_startup(self) -> bool:
        return self.database_schema_mode == "create"
