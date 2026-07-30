from __future__ import annotations

import json

from app.modules.admin.services import system_update_service as service


def test_browser_update_status_excludes_detailed_host_output(tmp_path, monkeypatch) -> None:
    request_dir = tmp_path / "requests"
    status_dir = tmp_path / "status"
    request_dir.mkdir()
    status_dir.mkdir()
    (status_dir / service.STATUS_FILE).write_text(
        json.dumps(
            {
                "state": "failed",
                "operation": "update_migrate",
                "message": "private path /srv/secret and token=do-not-return",
                "requested_by": "private-admin-name",
                "requested_at": "2026-07-30T10:00:00+00:00",
                "started_at": "2026-07-30T10:01:00+00:00",
                "finished_at": "2026-07-30T10:02:00+00:00",
                "commit_before": "abc123",
                "commit_after": "def456",
            }
        ),
        encoding="utf-8",
    )
    (status_dir / "update.log").write_text("private log line\n", encoding="utf-8")
    monkeypatch.setattr(service, "_request_dir", lambda: request_dir)
    monkeypatch.setattr(service, "_status_dir", lambda: status_dir)

    public = service.get_system_update_status().model_dump()
    assert public["message"] == "The update failed. Review the configured webhook or host logs."
    for field in ("requested_by", "heartbeat_at", "commit_before", "commit_after", "log_tail"):
        assert field not in public
    assert "secret" not in json.dumps(public)

    internal = service.get_system_update_internal_status()
    assert internal.requested_by == "private-admin-name"
    assert internal.commit_after == "def456"
    assert "token=do-not-return" in internal.message
