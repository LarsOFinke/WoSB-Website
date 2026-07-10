from __future__ import annotations

import os
from pathlib import Path
import tomllib
from typing import Any

from app.core.config_error import ConfigError
from app.core.runtime_paths import normalize_database_url, resolve_runtime_path
from app.core.settings_model import Settings


BACKEND_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ENV_FILE = BACKEND_ROOT / ".env"
DEFAULT_CFG_FILE = BACKEND_ROOT / "config" / "app.toml"


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            raise ConfigError(f"Invalid env line in {path}:{line_number}; expected KEY=value.")
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or not key.replace("_", "").isalnum() or key[0].isdigit():
            raise ConfigError(f"Invalid env key in {path}:{line_number}: {key!r}.")
        values[key] = _strip_quotes(value)
    return values


def _load_required_env_file() -> dict[str, str]:
    env_path = Path(os.environ.get("WOSB_ENV_FILE", DEFAULT_ENV_FILE)).expanduser()
    if not env_path.exists():
        raise ConfigError(
            f"Missing required env file: {env_path}. "
            "Copy backend/.env.example to backend/.env or set WOSB_ENV_FILE."
        )
    if not env_path.is_file():
        raise ConfigError(f"Env path is not a file: {env_path}")
    return _parse_env_file(env_path)


def _load_required_cfg() -> dict[str, Any]:
    cfg_path = Path(os.environ.get("WOSB_CONFIG_FILE", DEFAULT_CFG_FILE)).expanduser()
    if not cfg_path.exists():
        raise ConfigError(
            f"Missing required config file: {cfg_path}. "
            "Keep backend/config/app.toml in the deployment or set WOSB_CONFIG_FILE."
        )
    if not cfg_path.is_file():
        raise ConfigError(f"Config path is not a file: {cfg_path}")
    with cfg_path.open("rb") as handle:
        return tomllib.load(handle)


_ENV_FILE_VALUES = _load_required_env_file()
_CFG = _load_required_cfg()


def _cfg(section: str, key: str) -> Any:
    try:
        value = _CFG[section][key]
    except KeyError as exc:
        raise ConfigError(f"Missing required config value [{section}].{key}.") from exc
    if isinstance(value, str) and not value.strip():
        raise ConfigError(f"Config value [{section}].{key} must not be empty.")
    return value


def _env(name: str, *, required: bool = True) -> str:
    value = os.environ.get(name, _ENV_FILE_VALUES.get(name))
    if required and (value is None or not str(value).strip()):
        raise ConfigError(f"Missing required environment value: {name}.")
    return str(value).strip() if value is not None else ""


def _bool(value: str, *, name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(f"{name} must be a boolean value, got {value!r}.")


def _bool_env(name: str) -> bool:
    return _bool(_env(name), name=name)


def _split_csv(value: str, *, name: str) -> list[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        raise ConfigError(f"{name} must contain at least one value.")
    return items


def _int_cfg(section: str, key: str) -> int:
    value = _cfg(section, key)
    if not isinstance(value, int):
        raise ConfigError(f"Config value [{section}].{key} must be an integer.")
    return value


def _bool_cfg(section: str, key: str) -> bool:
    value = _cfg(section, key)
    if not isinstance(value, bool):
        raise ConfigError(f"Config value [{section}].{key} must be boolean.")
    return value


def _upper_cfg(section: str, key: str) -> str:
    return str(_cfg(section, key)).upper()


def _lower_cfg(section: str, key: str) -> str:
    return str(_cfg(section, key)).lower()


def _weak_seed_password(password: str) -> bool:
    weak = {
        "admin",
        "admin123",
        "password",
        "changeme",
        "change_me",
        "CHANGE_ME_USE_A_LONG_RANDOM_PASSWORD",
    }
    return password in weak or len(password) < 12


def _build_settings() -> Settings:
    environment = _env("APP_ENV").lower()
    if environment not in {"development", "staging", "production"}:
        raise ConfigError("APP_ENV must be one of: development, staging, production.")

    log_format = _lower_cfg("logging", "format")
    if log_format not in {"plain", "json"}:
        raise ConfigError("[logging].format must be plain or json.")

    cookie_samesite = _lower_cfg("session", "cookie_samesite")
    if cookie_samesite not in {"lax", "strict", "none"}:
        raise ConfigError("[session].cookie_samesite must be lax, strict or none.")

    auto_seed = _bool_env("AUTO_SEED")
    seed_username = _env("SEED_ADMIN_USERNAME", required=auto_seed)
    seed_password = _env("SEED_ADMIN_PASSWORD", required=auto_seed)
    seed_display_name = _env("SEED_ADMIN_DISPLAY_NAME", required=auto_seed)
    if auto_seed and _weak_seed_password(seed_password):
        raise ConfigError(
            "SEED_ADMIN_PASSWORD must be changed to a strong non-default value before startup."
        )

    cookie_secure = _bool_env("SESSION_COOKIE_SECURE")
    if environment == "production" and not cookie_secure:
        raise ConfigError("SESSION_COOKIE_SECURE must be true when APP_ENV=production.")

    return Settings(
        app_name=str(_cfg("app", "name")),
        app_version=str(_cfg("app", "version")),
        environment=environment,
        api_prefix=str(_cfg("app", "api_prefix")),
        database_url=normalize_database_url(_env("DATABASE_URL"), base_dir=BACKEND_ROOT),
        upload_dir=str(
            resolve_runtime_path(
                _env("UPLOAD_DIR"),
                base_dir=BACKEND_ROOT,
                setting_name="UPLOAD_DIR",
            )
        ),
        auto_seed=auto_seed,
        log_level=_upper_cfg("logging", "level"),
        log_format=log_format,
        sql_log_level=_upper_cfg("logging", "sql_level"),
        db_logging_enabled=_bool_cfg("logging", "db_enabled"),
        db_log_level=_upper_cfg("logging", "db_level"),
        console_logging_enabled=_bool_cfg("logging", "console_enabled"),
        session_cookie_name=str(_cfg("session", "cookie_name")),
        session_cookie_secure=cookie_secure,
        session_cookie_samesite=cookie_samesite,
        session_ttl_hours=_int_cfg("session", "ttl_hours"),
        seed_admin_username=seed_username,
        seed_admin_password=seed_password,
        seed_admin_display_name=seed_display_name,
        cors_origins=_split_csv(_env("CORS_ORIGINS"), name="CORS_ORIGINS"),
        upload_image_limit_mb=_int_cfg("upload_limits", "image_mb"),
        upload_document_limit_mb=_int_cfg("upload_limits", "document_mb"),
        upload_video_limit_mb=_int_cfg("upload_limits", "video_mb"),
    )


settings = _build_settings()
