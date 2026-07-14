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


def _control_dir() -> Path:
    path = Path(settings.control_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


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


def _write_json_atomic(path: Path, payload: dict, mode: int) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.chmod(mode)
    os.replace(temporary, path)
    path.chmod(mode)


def get_discord_bot_status() -> DiscordBotStatus:
    directory = _control_dir()
    payload = _read_json(directory / STATUS_FILE)
    state = str(payload.get("state") or "idle")
    configuration_payload = payload.get("configuration")
    if not isinstance(configuration_payload, dict):
        configuration_payload = {}
    return DiscordBotStatus(
        state=state,
        operation=str(payload.get("operation") or "status"),
        message=str(payload.get("message") or "Discord bot management has not been configured yet."),
        configured=bool(payload.get("configured", False)),
        installed=bool(payload.get("installed", False)),
        service_state=str(payload.get("service_state") or "unknown"),
        version=payload.get("version"),
        commit=payload.get("commit"),
        requested_by=payload.get("requested_by"),
        requested_at=payload.get("requested_at"),
        started_at=payload.get("started_at"),
        finished_at=payload.get("finished_at"),
        log_tail=_log_tail(directory / LOG_FILE),
        request_available=not (directory / REQUEST_FILE).exists() and state not in ACTIVE_STATES,
        configuration=DiscordBotConfigurationStatus.model_validate(configuration_payload),
    )


def _queue_request(user: User, *, operation: str, request_payload: dict) -> DiscordBotStatus:
    directory = _control_dir()
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
    queued_status = {
        **current.model_dump(exclude={"log_tail", "request_available"}),
        "state": "queued",
        "operation": operation,
        "message": "Discord bot operation accepted and waiting for the host runner.",
        "requested_by": user.username,
        "requested_at": now,
        "started_at": None,
        "finished_at": None,
    }

    _write_json_atomic(directory / STATUS_FILE, queued_status, 0o664)
    _write_json_atomic(request_path, payload, 0o600)
    return get_discord_bot_status()


def request_discord_bot_operation(user: User, operation: DiscordBotOperation) -> DiscordBotStatus:
    current = get_discord_bot_status()
    if operation not in {"install", "refresh"} and not current.installed:
        raise DiscordBotManagerError("The Discord bot must be installed before this operation can run.")
    return _queue_request(user, operation=operation, request_payload={})


def request_discord_bot_configuration(
    user: User,
    configuration: DiscordBotConfigurationUpdate,
) -> DiscordBotStatus:
    current = get_discord_bot_status()
    if not current.installed:
        raise DiscordBotManagerError("The Discord bot must be installed before it can be configured.")
    if not configuration.discord_bot_token and not current.configuration.discord_token_configured:
        raise DiscordBotManagerError("A Discord bot token is required for the initial configuration.")
    if not configuration.webhook_secret and not current.configuration.webhook_secret_configured:
        raise DiscordBotManagerError("A website webhook signing secret is required for the initial configuration.")
    return _queue_request(
        user,
        operation="configure",
        request_payload={
            "configuration": configuration.model_dump(exclude_none=True),
        },
    )
