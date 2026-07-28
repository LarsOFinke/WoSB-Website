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
