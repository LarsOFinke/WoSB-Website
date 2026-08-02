import json

import pytest

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
