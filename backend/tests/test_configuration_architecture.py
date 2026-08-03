from __future__ import annotations

from pathlib import Path

import pytest

from app.configuration.loader import SettingsLoader
from app.configuration.paths import ConfigurationPaths
from app.configuration.sources.ini_config_source import IniConfigSource
from app.core.config_error import ConfigError


def _write_config(config_dir: Path) -> None:
    config_dir.mkdir()
    (config_dir / "application.cfg").write_text(
        "[app]\nname = Test Fleet\nversion = 2.0\napi_prefix = /test\n",
        encoding="utf-8",
    )
    (config_dir / "logging.cfg").write_text(
        "[logging]\nlevel=INFO\nformat=json\nsql_level=WARNING\n"
        "db_enabled=false\ndb_level=ERROR\nconsole_enabled=true\n",
        encoding="utf-8",
    )
    (config_dir / "session.cfg").write_text(
        "[session]\ncookie_name=test_session\ncookie_samesite=strict\nttl_hours=12\n",
        encoding="utf-8",
    )
    (config_dir / "uploads.cfg").write_text(
        "[upload_limits]\nimage_mb=2\ndocument_mb=3\nvideo_mb=4\n",
        encoding="utf-8",
    )


def _write_env(path: Path, root: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "APP_ENV=development",
                f"DATABASE_URL=sqlite:///{root / 'app.db'}",
                "DB_SCHEMA_MODE=create",
                f"UPLOAD_DIR={root / 'uploads'}",
                f"CONTROL_DIR={root / 'control'}",
                "CORS_ORIGINS=https://one.example,https://two.example",
                "SESSION_COOKIE_SECURE=false",
                "AUTO_SEED=false",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_settings_loader_composes_multiple_cfg_files(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    env_file = tmp_path / ".env"
    _write_config(config_dir)
    _write_env(env_file, tmp_path)

    settings = SettingsLoader(
        ConfigurationPaths(tmp_path, env_file, config_dir)
    ).load()

    assert settings.app_name == "Test Fleet"
    assert settings.logging.format == "json"
    assert settings.session.ttl_hours == 12
    assert settings.upload_limits.video_mb == 4
    assert settings.cors_origins == (
        "https://one.example",
        "https://two.example",
    )


def test_process_environment_overrides_dotenv_values(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    env_file = tmp_path / ".env"
    _write_config(config_dir)
    _write_env(env_file, tmp_path)

    settings = SettingsLoader(
        ConfigurationPaths(tmp_path, env_file, config_dir),
        environ={"APP_ENV": "staging"},
    ).load()

    assert settings.environment == "staging"


def test_process_environment_overrides_session_cfg_values(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    env_file = tmp_path / ".env"
    _write_config(config_dir)
    _write_env(env_file, tmp_path)

    settings = SettingsLoader(
        ConfigurationPaths(
            tmp_path,
            env_file,
            config_dir,
        ),
        environ={
            "APP_ENV": "staging",
            "SESSION_COOKIE_NAME": "fleet_session",
            "SESSION_COOKIE_SAMESITE": "strict",
            "SESSION_TTL_HOURS": "12",
        },
    ).load()

    assert settings.session_cookie_name == "fleet_session"
    assert settings.session_cookie_samesite == "strict"
    assert settings.session_ttl_hours == 12


def test_ini_source_rejects_toml_files(tmp_path: Path) -> None:
    path = tmp_path / "app.toml"
    path.write_text("[app]\nname='legacy'\n", encoding="utf-8")

    with pytest.raises(ConfigError, match=".cfg extension"):
        IniConfigSource(path)


def test_retention_settings_reject_non_positive_values(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    env_file = tmp_path / ".env"
    _write_config(config_dir)
    _write_env(env_file, tmp_path)
    uploads = config_dir / "uploads.cfg"
    uploads.write_text(
        uploads.read_text(encoding="utf-8")
        + "\n[maintenance]\nwebhook_delivery_retention_days=0\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="webhook_delivery_retention_days.*greater than zero"):
        SettingsLoader(ConfigurationPaths(tmp_path, env_file, config_dir)).load()


def test_webhook_encryption_key_ring_is_loaded_and_validated(tmp_path: Path) -> None:
    from cryptography.fernet import Fernet

    config_dir = tmp_path / "config"
    env_file = tmp_path / ".env"
    _write_config(config_dir)
    _write_env(env_file, tmp_path)
    first = Fernet.generate_key().decode("ascii")
    second = Fernet.generate_key().decode("ascii")
    env_file.write_text(
        env_file.read_text(encoding="utf-8")
        + f"WEBHOOK_ENCRYPTION_KEYS={first},{second}\n",
        encoding="utf-8",
    )

    settings = SettingsLoader(ConfigurationPaths(tmp_path, env_file, config_dir)).load()

    assert settings.webhook_encryption_keys == (first, second)


def test_webhook_encryption_key_ring_rejects_non_fernet_base64(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    env_file = tmp_path / ".env"
    _write_config(config_dir)
    _write_env(env_file, tmp_path)
    env_file.write_text(
        env_file.read_text(encoding="utf-8")
        + "WEBHOOK_ENCRYPTION_KEYS=!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="URL-safe Base64 Fernet keys"):
        SettingsLoader(ConfigurationPaths(tmp_path, env_file, config_dir)).load()


def test_legal_notice_defaults_are_loaded_from_environment(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    env_file = tmp_path / ".env"
    _write_config(config_dir)
    _write_env(env_file, tmp_path)
    env_file.write_text(
        env_file.read_text(encoding="utf-8")
        + "LEGAL_NOTICE_PROVIDER_NAME=Example Community\n"
        + "LEGAL_NOTICE_EMAIL=legal@example.invalid\n",
        encoding="utf-8",
    )

    settings = SettingsLoader(ConfigurationPaths(tmp_path, env_file, config_dir)).load()

    assert settings.legal_notice.published is False
    assert settings.legal_notice.provider_name == "Example Community"
    assert settings.legal_notice.email == "legal@example.invalid"
    assert settings.legal_notice.country == "Deutschland"


def test_published_legal_notice_rejects_incomplete_environment_values(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    env_file = tmp_path / ".env"
    _write_config(config_dir)
    _write_env(env_file, tmp_path)
    env_file.write_text(
        env_file.read_text(encoding="utf-8")
        + "LEGAL_NOTICE_PUBLISHED=true\n"
        + "LEGAL_NOTICE_PROVIDER_NAME=Incomplete Provider\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="complete provider details"):
        SettingsLoader(ConfigurationPaths(tmp_path, env_file, config_dir)).load()
