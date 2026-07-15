from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path

from app.core.config import settings
from app.modules.accounts.models.user import User
from app.modules.admin.schemas.discord_bot import (
    DiscordBotConfigurationStatus,
    DiscordBotConfigurationUpdate,
    DiscordBotOperation,
    DiscordBotStatus,
)


ACTIVE_STATES = {"queued", "running"}
STATUS_FILE = "discord-bot-status.json"
REQUEST_FILE = "discord-bot.request"
LOG_FILE = "discord-bot.log"


class DiscordBotManagerError(RuntimeError):
    pass


def _request_dir() -> Path:
    path = Path(settings.control_request_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _status_dir() -> Path:
    return Path(settings.control_status_dir)


def _read_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _log_tail(path: Path, limit: int = 100) -> list[str]:
    if not path.is_file():
        return []
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
    except OSError:
        return []


def _write_request_atomic(path: Path, payload: dict) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.chmod(0o600)
    os.replace(temporary, path)
    path.chmod(0o600)


def get_discord_bot_status() -> DiscordBotStatus:
    request_path = _request_dir() / REQUEST_FILE
    payload = _read_json(_status_dir() / STATUS_FILE)
    request_payload = _read_json(request_path)
    state = str(payload.get("state") or "idle")
    if request_payload and state not in ACTIVE_STATES:
        state = "queued"
        payload = {
            **payload,
            "state": "queued",
            "operation": request_payload.get("operation") or "status",
            "message": "Discord bot operation accepted and waiting for the host runner.",
            "requested_by": request_payload.get("requested_by"),
            "requested_at": request_payload.get("requested_at"),
            "started_at": None,
            "finished_at": None,
        }

    configuration_payload = payload.get("configuration")
    if not isinstance(configuration_payload, dict):
        configuration_payload = {}
    return DiscordBotStatus(
        state=state,
        operation=str(payload.get("operation") or "status"),
        message=str(
            payload.get("message")
            or "Discord bot management has not been configured yet."
        ),
        configured=bool(payload.get("configured", False)),
        installed=bool(payload.get("installed", False)),
        service_state=str(payload.get("service_state") or "unknown"),
        version=payload.get("version"),
        commit=payload.get("commit"),
        requested_by=payload.get("requested_by"),
        requested_at=payload.get("requested_at"),
        started_at=payload.get("started_at"),
        finished_at=payload.get("finished_at"),
        log_tail=_log_tail(_status_dir() / LOG_FILE),
        request_available=not request_path.exists() and state not in ACTIVE_STATES,
        configuration=DiscordBotConfigurationStatus.model_validate(configuration_payload),
    )


def _queue_request(user: User, *, operation: str, request_payload: dict) -> DiscordBotStatus:
    directory = _request_dir()
    request_path = directory / REQUEST_FILE
    current = get_discord_bot_status()
    if request_path.exists() or current.state in ACTIVE_STATES:
        raise DiscordBotManagerError("A Discord bot operation is already queued or running.")

    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "requested_by": user.username,
        "requested_at": now,
        "operation": operation,
        **request_payload,
    }
    _write_request_atomic(request_path, payload)
    return get_discord_bot_status()


def request_discord_bot_operation(
    user: User, operation: DiscordBotOperation
) -> DiscordBotStatus:
    current = get_discord_bot_status()
    if operation not in {"install", "refresh"} and not current.installed:
        raise DiscordBotManagerError(
            "The Discord bot must be installed before this operation can run."
        )
    return _queue_request(user, operation=operation, request_payload={})


def request_discord_bot_configuration(
    user: User,
    configuration: DiscordBotConfigurationUpdate,
) -> DiscordBotStatus:
    current = get_discord_bot_status()
    if not current.installed:
        raise DiscordBotManagerError(
            "The Discord bot must be installed before it can be configured."
        )
    if not configuration.discord_bot_token and not current.configuration.discord_token_configured:
        raise DiscordBotManagerError(
            "A Discord bot token is required for the initial configuration."
        )
    if not configuration.webhook_secret and not current.configuration.webhook_secret_configured:
        raise DiscordBotManagerError(
            "A website webhook signing secret is required for the initial configuration."
        )
    return _queue_request(
        user,
        operation="configure",
        request_payload={
            "configuration": configuration.model_dump(exclude_none=True),
        },
    )
