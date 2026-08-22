from __future__ import annotations

import json

import pytest

from rbf_recovery_tool.enrollment import discover_response, load_response, validate_response


def _response() -> dict[str, object]:
    return {
        "schema_version": 1,
        "kind": "rbf-backup-enrollment-response",
        "enrollment_id": "A" * 32,
        "deployment_environment": "production",
        "host": "backup.example.net",
        "port": 22,
        "username": "rbf-backup-production",
        "recovery_username": "rbf-recovery-production",
        "storage_directory": "/backups/wosb/production",
        "remote_directory": "/incoming",
        "receipt_directory": "/receipts",
        "recovery_directory": "/data",
        "host_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBackupHostKey=",
        "host_key_fingerprint": "SHA256:" + "A" * 43,
        "age_recipient": "age1" + "a" * 58,
        "managed_server": True,
        "trust_model": "server-controlled-ingest-v1",
    }


def test_response_preserves_loopback_recovery_account() -> None:
    response = validate_response(_response())
    assert response["username"] == "rbf-backup-production"
    assert response["recovery_username"] == "rbf-recovery-production"
    assert response["recovery_directory"] == "/data"


def test_response_rejects_cross_environment_identity() -> None:
    payload = {**_response(), "deployment_environment": "test"}
    with pytest.raises(ValueError, match="identity does not match"):
        validate_response(payload)


def test_response_json_is_validated(tmp_path) -> None:
    path = tmp_path / "response.json"
    path.write_text(json.dumps(_response()), encoding="utf-8")
    assert load_response(path)["enrollment_id"] == "A" * 32

    path.write_text(json.dumps({"kind": "wrong"}), encoding="utf-8")
    with pytest.raises(RuntimeError, match="Invalid enrollment response"):
        load_response(path)


def test_request_file_explains_that_provisioning_must_run_first(tmp_path) -> None:
    path = tmp_path / "whatever-name.json"
    path.write_text(json.dumps({"schema_version": 1, "kind": "rbf-backup-enrollment-request"}))
    with pytest.raises(RuntimeError, match="request, not a response"):
        load_response(path)


def test_response_discovery_uses_content_instead_of_filename(tmp_path) -> None:
    request = tmp_path / "response-looking-name.json"
    request.write_text(json.dumps({"schema_version": 1, "kind": "rbf-backup-enrollment-request"}))
    response = tmp_path / "no-required-filename.json"
    response.write_text(json.dumps(_response()))

    assert discover_response(tmp_path) == response


def test_response_discovery_requires_explicit_selection_for_multiple_targets(tmp_path) -> None:
    (tmp_path / "test.json").write_text(json.dumps(_response()))
    (tmp_path / "production.json").write_text(
        json.dumps({**_response(), "enrollment_id": "B" * 32})
    )
    with pytest.raises(RuntimeError, match="Multiple valid enrollment responses"):
        discover_response(tmp_path)


def test_response_discovery_reports_when_only_a_request_exists(tmp_path) -> None:
    request = tmp_path / "misnamed.json"
    request.write_text(json.dumps({"schema_version": 1, "kind": "rbf-backup-enrollment-request"}))
    with pytest.raises(RuntimeError, match="Only an enrollment request was found"):
        discover_response(tmp_path)
