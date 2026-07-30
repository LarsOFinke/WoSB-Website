from types import SimpleNamespace

from app.modules.admin.services import system_update_webhook_service as service
from app.modules.admin.services.webhook_event_catalog import EVENT_TYPES
from app.modules.admin.services.webhook_message_templates import DEFAULT_MESSAGES


def test_server_update_events_are_configurable_webhook_events() -> None:
    assert {"system.update.started", "system.update.result"}.issubset(EVENT_TYPES)
    assert "Server Operation Started" in DEFAULT_MESSAGES["system.update.started"]
    assert "Server Operation Result" in DEFAULT_MESSAGES["system.update.result"]


def test_completed_update_result_is_queued_only_once(tmp_path, monkeypatch) -> None:
    terminal = SimpleNamespace(
        state="succeeded",
        operation="update_migrate",
        requested_by="captain",
        requested_at="2026-07-29T12:00:00Z",
        started_at="2026-07-29T12:01:00Z",
        finished_at="2026-07-29T12:03:00Z",
        commit_before="abc",
        commit_after="def",
        message="Update completed.",
    )
    monkeypatch.setattr(service, "_control_dir", lambda: tmp_path)
    monkeypatch.setattr(service, "get_system_update_internal_status", lambda: terminal)
    queued = []

    def fake_queue(_db, **payload):
        queued.append(payload)
        return [17]

    monkeypatch.setattr(service, "queue_webhook_event", fake_queue)
    assert service.queue_pending_system_update_result(object()) == [17]
    assert service.queue_pending_system_update_result(object()) == []
    assert queued[0]["event_type"] == "system.update.result"
    assert queued[0]["data"]["state"] == "succeeded"


def test_failed_result_queue_is_retried_without_writing_marker(tmp_path, monkeypatch) -> None:
    terminal = SimpleNamespace(
        state="failed",
        operation="update_migrate",
        requested_by="captain",
        requested_at="2026-07-29T12:00:00Z",
        started_at="2026-07-29T12:01:00Z",
        finished_at="2026-07-29T12:03:00Z",
        commit_before="abc",
        commit_after="abc",
        message="Update failed.",
    )
    monkeypatch.setattr(service, "_control_dir", lambda: tmp_path)
    monkeypatch.setattr(service, "get_system_update_internal_status", lambda: terminal)

    class FakeDb:
        rolled_back = False

        def rollback(self):
            self.rolled_back = True

    db = FakeDb()
    monkeypatch.setattr(service, "queue_webhook_event", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("db unavailable")))

    assert service.queue_pending_system_update_result(db) == []
    assert db.rolled_back is True
    assert not (tmp_path / service._RESULT_MARKER_FILE).exists()
    assert not list(tmp_path.glob(".update-webhook-result-*.claim"))
