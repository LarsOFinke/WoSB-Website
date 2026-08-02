import json
import sys

import pytest

from app.cli.maintenance_mode import main
from app.core.maintenance_event_outbox import MaintenanceEventOutbox
from app.core.service_availability import ServiceAvailability


def test_maintenance_mode_is_written_atomically_and_removed_idempotently(tmp_path) -> None:
    service = ServiceAvailability(tmp_path / "status")

    state = service.enable(
        reason="update", message="  Installing   update.  ", retry_after_seconds=5
    )

    assert state.message == "Installing update."
    assert state.retry_after_seconds == 30
    assert service.read() == state
    assert json.loads(service.path.read_text(encoding="utf-8"))["reason"] == "update"
    assert not list(service.status_dir.glob("*.tmp"))
    assert service.disable() is True
    assert service.disable() is False


def test_maintenance_mode_rejects_unbounded_or_unknown_content(tmp_path) -> None:
    service = ServiceAvailability(tmp_path)

    with pytest.raises(ValueError, match="Unsupported"):
        service.enable(reason="tracking", message="No")
    with pytest.raises(ValueError, match="1 to 240"):
        service.enable(reason="manual", message=" ")


def test_manual_cli_persists_started_and_successful_end_events(tmp_path, monkeypatch) -> None:
    status_dir = tmp_path / "status"
    event_dir = tmp_path / "inbox"
    common = ["rbf-maintenance", "--status-dir", str(status_dir), "--event-dir", str(event_dir)]

    monkeypatch.setattr(sys, "argv", [common[0], "enable", *common[1:], "--reason", "manual"])
    main()
    monkeypatch.setattr(sys, "argv", [common[0], "disable", *common[1:]])
    main()

    events = [MaintenanceEventOutbox.read(path) for path in MaintenanceEventOutbox(event_dir).pending_paths()]
    assert [event.action for event in events] == ["started", "ended"]
    assert events[0].reason == events[1].reason == "manual"
    assert events[1].outcome == "succeeded"
