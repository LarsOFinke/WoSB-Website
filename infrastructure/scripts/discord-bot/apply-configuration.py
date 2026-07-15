#!/usr/bin/env python3
"""Validate and atomically persist host-managed Discord bot configuration."""

from __future__ import annotations

from datetime import datetime, timezone
import grp
import json
import os
from pathlib import Path
import secrets
import sys
from urllib.parse import urlsplit

import yaml
from rbf_discord_bot.config import BotConfig


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def valid_secret(value: str, minimum: int) -> bool:
    return (
        len(value) >= minimum
        and not value.startswith("CHANGE_ME")
        and "#" not in value
        and not any(character.isspace() for character in value)
    )


def atomic_write(path: Path, content: str, *, mode: int = 0o640) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name("." + path.name + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    os.chmod(temporary, mode)
    try:
        group_id = grp.getgrnam("rbf-discord").gr_gid
        os.chown(temporary, 0, group_id)
    except KeyError:
        pass
    os.replace(temporary, path)
    os.chmod(path, mode)


def read_configuration(request_path: Path) -> dict[str, object]:
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    configuration = payload.get("configuration")
    if not isinstance(configuration, dict):
        raise SystemExit("Missing Discord bot configuration payload.")
    return configuration


def validate_website_base_url(configuration: dict[str, object]) -> str:
    website_base_url = str(configuration.get("website_base_url") or "").strip().rstrip("/")
    parsed_url = urlsplit(website_base_url)
    invalid = (
        parsed_url.scheme != "https"
        or not parsed_url.hostname
        or parsed_url.username
        or parsed_url.password
        or parsed_url.query
        or parsed_url.fragment
        or parsed_url.path not in {"", "/"}
    )
    if invalid:
        raise SystemExit(
            "The website base URL must be an absolute HTTPS URL without credentials, query or fragment."
        )
    return website_base_url


def resolve_secrets(
    configuration: dict[str, object], existing_env: dict[str, str]
) -> tuple[str, str, str]:
    discord_token = str(
        configuration.get("discord_bot_token") or existing_env.get("DISCORD_BOT_TOKEN") or ""
    ).strip()
    webhook_secret = str(
        configuration.get("webhook_secret") or existing_env.get("RBF_WEBHOOK_SECRET") or ""
    ).strip()
    management_token = str(existing_env.get("BOT_MANAGEMENT_TOKEN") or "").strip()

    if not valid_secret(discord_token, 20):
        raise SystemExit("A valid Discord bot token is required.")
    if not valid_secret(webhook_secret, 32):
        raise SystemExit("A webhook signing secret with at least 32 characters is required.")
    if not valid_secret(management_token, 32):
        management_token = secrets.token_urlsafe(48)
    return discord_token, webhook_secret, management_token


def build_bot_config(
    configuration: dict[str, object],
    source_path: Path,
    website_base_url: str,
) -> BotConfig:
    raw_config = yaml.safe_load(source_path.read_text(encoding="utf-8")) or {}
    raw_config.setdefault("server", {})
    raw_config["server"]["host"] = os.environ["RBF_DISCORD_BOT_BIND_HOST"]
    raw_config["server"]["port"] = int(os.environ.get("RBF_DISCORD_BOT_PORT", "8765"))
    raw_config["server"]["public_webhook_path"] = "/webhooks/rbf"
    raw_config.setdefault("security", {})
    raw_config["security"]["timestamp_tolerance_seconds"] = int(
        configuration.get("timestamp_tolerance_seconds", 300)
    )
    raw_config["security"]["management_token_header"] = "X-RBF-Bot-Token"
    raw_config["website"] = {"base_url": website_base_url}
    raw_config.setdefault("discord", {})
    raw_config["discord"]["api_base_url"] = "https://discord.com/api/v10"
    raw_config["discord"]["request_timeout_seconds"] = float(
        configuration.get("request_timeout_seconds", 15)
    )
    raw_config["discord"]["max_attempts"] = int(configuration.get("max_attempts", 3))
    raw_config["discord"]["suppress_notifications"] = bool(
        configuration.get("suppress_notifications", False)
    )
    return BotConfig.model_validate(raw_config)


def main() -> None:
    if len(sys.argv) != 6:
        raise SystemExit(
            "Usage: apply-configuration.py REQUEST INSTALL_DIR ENV_FILE CONFIG_FILE SUMMARY_FILE"
        )

    request_path, install_dir, env_path, config_path, summary_path = map(Path, sys.argv[1:])
    configuration = read_configuration(request_path)
    existing_env = parse_env(env_path)
    discord_token, webhook_secret, management_token = resolve_secrets(configuration, existing_env)
    website_base_url = validate_website_base_url(configuration)
    example_path = install_dir / "config" / "bot.yaml.example"
    source_path = config_path if config_path.is_file() else example_path
    validated = build_bot_config(configuration, source_path, website_base_url)

    config_content = yaml.safe_dump(
        validated.model_dump(mode="json"), sort_keys=False, allow_unicode=True
    )
    env_content = "\n".join(
        [
            "# Managed through the Royal Blackwater Fleet administrator panel.",
            "DISCORD_BOT_TOKEN=" + discord_token,
            "RBF_WEBHOOK_SECRET=" + webhook_secret,
            "BOT_MANAGEMENT_TOKEN=" + management_token,
            "RBF_BOT_CONFIG=/etc/rbf-discord-bot/bot.yaml",
            "RBF_BOT_DATA_DIR=/var/lib/rbf-discord-bot",
            "RBF_BOT_LOG_LEVEL=INFO",
            "",
        ]
    )
    atomic_write(env_path, env_content)
    atomic_write(config_path, config_content)

    summary = {
        "ready": True,
        "env_file_present": True,
        "config_file_present": True,
        "discord_token_configured": True,
        "webhook_secret_configured": True,
        "management_token_configured": True,
        "website_base_url": website_base_url,
        "suppress_notifications": validated.discord.suppress_notifications,
        "timestamp_tolerance_seconds": validated.security.timestamp_tolerance_seconds,
        "request_timeout_seconds": validated.discord.request_timeout_seconds,
        "max_attempts": validated.discord.max_attempts,
        "bind_host": validated.server.host,
        "listen_port": validated.server.port,
        "firewall_mode": os.environ["RBF_DISCORD_BOT_FIREWALL_MODE"],
        "public_webhook_path": validated.server.public_webhook_path,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "valid": True,
        "message": "Configuration validated and written by the host runner.",
    }
    atomic_write(summary_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print("true" if bool(configuration.get("restart_after_save", True)) else "false")


if __name__ == "__main__":
    main()
