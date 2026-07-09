from dataclasses import dataclass, field
import os


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Iron Crown Fleet Hub")
    app_version: str = os.getenv("APP_VERSION", "0.8.0")
    environment: str = os.getenv("APP_ENV", "development")
    api_prefix: str = os.getenv("API_PREFIX", "/api")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./wosb_minimal.db")
    upload_dir: str = os.getenv("UPLOAD_DIR", "storage/uploads")
    auto_seed: bool = _bool_env("AUTO_SEED", True)

    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format: str = os.getenv("LOG_FORMAT", "plain").lower()
    sql_log_level: str = os.getenv("SQL_LOG_LEVEL", "WARNING").upper()
    db_logging_enabled: bool = _bool_env("DB_LOGGING_ENABLED", True)
    db_log_level: str = os.getenv("DB_LOG_LEVEL", "INFO").upper()
    console_logging_enabled: bool = _bool_env("CONSOLE_LOGGING_ENABLED", False)

    session_cookie_name: str = os.getenv("SESSION_COOKIE_NAME", "wosb_session")
    session_cookie_secure: bool = _bool_env("SESSION_COOKIE_SECURE", False)
    session_cookie_samesite: str = os.getenv("SESSION_COOKIE_SAMESITE", "lax")
    session_ttl_hours: int = int(os.getenv("SESSION_TTL_HOURS", "24"))

    seed_admin_username: str = os.getenv("SEED_ADMIN_USERNAME", "admin")
    seed_admin_password: str = os.getenv("SEED_ADMIN_PASSWORD", "admin123")
    seed_admin_display_name: str = os.getenv("SEED_ADMIN_DISPLAY_NAME", "Community Admin")

    cors_origins: list[str] = field(
        default_factory=lambda: _split_csv(
            os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
        )
    )

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


settings = Settings()
