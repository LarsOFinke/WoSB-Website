from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.accounts.models.user import User
from app.modules.admin.services.outbound_webhook_delivery_service import (
    attempt_webhook_delivery,
    queue_webhook_event,
    queue_webhook_event_safely,
    schedule_webhook_deliveries,
)
from app.modules.admin.services.system_update_service import get_system_update_status

_RESULT_MARKER_FILE = "update-webhook-result.json"
_TERMINAL_STATES = {"succeeded", "failed"}

logger = logging.getLogger(__name__)


def _control_dir() -> Path:
    path = Path(settings.control_request_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _read_marker() -> dict[str, object]:
    path = _control_dir() / _RESULT_MARKER_FILE
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_marker(signature: str) -> None:
    directory = _control_dir()
    path = directory / _RESULT_MARKER_FILE
    temporary = directory / f".{_RESULT_MARKER_FILE}.{os.getpid()}.tmp"
    temporary.write_text(
        json.dumps({"signature": signature}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.chmod(0o600)
    os.replace(temporary, path)
    path.chmod(0o600)


def _result_signature(status: object) -> str:
    payload = "|".join(
        str(getattr(status, field, "") or "")
        for field in (
            "state",
            "operation",
            "requested_at",
            "started_at",
            "finished_at",
            "commit_before",
            "commit_after",
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def queue_system_update_started(
    db: Session,
    *,
    actor: User,
    background_tasks: BackgroundTasks,
) -> list[int]:
    status = get_system_update_status()
    delivery_ids = queue_webhook_event_safely(
        db,
        event_type="system.update.started",
        resource_type="system_update",
        resource_id=status.requested_at or "queued",
        resource_url="/admin?section=status",
        actor=actor,
        scope_type="global",
        data={
            "state": status.state,
            "operation": status.operation,
            "requested_by": status.requested_by,
            "requested_at": status.requested_at,
            "message": status.message,
        },
    )
    schedule_webhook_deliveries(background_tasks, delivery_ids)
    return delivery_ids


def queue_pending_system_update_result(db: Session) -> list[int]:
    """Queue one terminal result event for the latest completed host update."""

    status = get_system_update_status()
    if status.state not in _TERMINAL_STATES or not status.finished_at:
        return []

    signature = _result_signature(status)
    if _read_marker().get("signature") == signature:
        return []

    directory = _control_dir()
    claim = directory / f".update-webhook-result-{signature}.claim"
    try:
        descriptor = os.open(claim, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return []
    else:
        os.close(descriptor)

    try:
        if _read_marker().get("signature") == signature:
            return []
        try:
            delivery_ids = queue_webhook_event(
                db,
                event_type="system.update.result",
                resource_type="system_update",
                resource_id=status.started_at or status.finished_at,
                resource_url="/admin?section=status",
                actor=None,
                scope_type="global",
                data={
                    "state": status.state,
                    "operation": status.operation,
                    "requested_by": status.requested_by,
                    "requested_at": status.requested_at,
                    "started_at": status.started_at,
                    "finished_at": status.finished_at,
                    "commit_before": status.commit_before,
                    "commit_after": status.commit_after,
                    "message": status.message,
                },
            )
        except Exception:  # pragma: no cover - retried by the next maintenance pass
            db.rollback()
            logger.exception("server update result webhook queue failed")
            return []
        _write_marker(signature)
        return delivery_ids
    finally:
        claim.unlink(missing_ok=True)


def deliver_pending_system_update_result() -> int:
    """Queue and synchronously deliver a pending result during maintenance/startup."""

    from app.db.session import SessionLocal

    with SessionLocal() as db:
        delivery_ids = queue_pending_system_update_result(db)
    for delivery_id in delivery_ids:
        attempt_webhook_delivery(delivery_id)
    return len(delivery_ids)
