from __future__ import annotations

import json

import pytest

from rbf_recovery_tool.enrollment import load_response, validate_response


def _response() -> dict[str, object]:
    return {
        "schema_version": 1,
        "kind": "rbf-backup-enrollment-response",
        "enrollment_id": "A" * 32,
        "host": "backup.example.net",
        "port": 22,
        "username": "rbf-backup",
        "recovery_username": "rbf-recovery",
        "remote_directory": "/data",
        "host_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBackupHostKey=",
        "host_key_fingerprint": "SHA256:" + "A" * 43,
        "age_recipient": "age1" + "a" * 58,
        "managed_server": True,
    }


def test_response_preserves_loopback_recovery_account() -> None:
    response = validate_response(_response())
    assert response["username"] == "rbf-backup"
    assert response["recovery_username"] == "rbf-recovery"


def test_response_json_is_validated(tmp_path) -> None:
    path = tmp_path / "response.json"
    path.write_text(json.dumps(_response()), encoding="utf-8")
    assert load_response(path)["enrollment_id"] == "A" * 32

    path.write_text(json.dumps({"kind": "wrong"}), encoding="utf-8")
    with pytest.raises(RuntimeError, match="Invalid enrollment response"):
        load_response(path)

