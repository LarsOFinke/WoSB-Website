from contextlib import nullcontext
from types import SimpleNamespace

from app.core.maintenance_event_outbox import MaintenanceEventOutbox
from app.modules.admin.services import maintenance_webhook_service as service
from app.modules.admin.services.webhook_event_catalog import EVENT_TYPES
from app.modules.admin.services.webhook_message_templates import DEFAULT_MESSAGES


def test_maintenance_events_are_configurable() -> None:
    expected = {"system.maintenance.started", "system.maintenance.ended"}
    assert expected.issubset(EVENT_TYPES)
    assert expected.issubset(DEFAULT_MESSAGES)


def test_pending_event_is_acknowledged_only_after_successful_queue(tmp_path, monkeypatch) -> None:
    outbox = MaintenanceEventOutbox(tmp_path)
    outbox.publish(
        action="ended",
        reason="restore",
        message="Restore failed and was rolled back.",
        started_at="2026-08-02T08:00:00+00:00",
        outcome="failed",
    )
    monkeypatch.setattr(service, "settings", SimpleNamespace(control_request_dir=str(tmp_path)))
    monkeypatch.setattr(service, "SessionLocal", lambda: nullcontext(object()))
    monkeypatch.setattr(
        service,
        "queue_webhook_event",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("database unavailable")),
    )

    assert service.deliver_pending_maintenance_events() == 0
    assert len(outbox.pending_paths()) == 1

    captured = []

    def queue(_db, **event):
        captured.append(event)
        return [41]

    attempted = []
    monkeypatch.setattr(service, "queue_webhook_event", queue)
    monkeypatch.setattr(service, "attempt_webhook_delivery", attempted.append)
    assert service.deliver_pending_maintenance_events() == 1
    assert outbox.pending_paths() == []
    assert captured[0]["event_type"] == "system.maintenance.ended"
    assert captured[0]["data"]["outcome"] == "failed"
    assert attempted == [41]
