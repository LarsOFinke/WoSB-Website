from dataclasses import dataclass, field
import os


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "WoSB Community Hub")
    app_version: str = os.getenv("APP_VERSION", "0.4.0")
    api_prefix: str = os.getenv("API_PREFIX", "/api")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./wosb_minimal.db")

    session_cookie_name: str = os.getenv("SESSION_COOKIE_NAME", "wosb_session")
    session_cookie_secure: bool = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
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


settings = Settings()
