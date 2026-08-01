from __future__ import annotations

import json
from pathlib import Path

from rbf_recovery_tool import server_setup


def test_server_provisioning_keeps_private_age_identity_local(tmp_path, monkeypatch) -> None:
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "kind": "rbf-backup-enrollment-request",
                "enrollment_id": "A" * 32,
                "ssh_public_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIProductKey= product",
                "requested_username": "rbf-backup",
                "requested_directory": "/data",
                "created_at": "2026-08-01T10:00:00+00:00",
                "product_hostname": "wosb-prod",
            }
        ),
        encoding="utf-8",
    )
    identity = tmp_path / "identity.txt"
    output = tmp_path / "response.json"
    provisioner = tmp_path / "Provision-RbfBackupServer.sh"
    provisioner.write_text("#!/bin/sh\n", encoding="utf-8")

    monkeypatch.setattr(server_setup, "support_script", lambda *_args, **_kwargs: provisioner)

    def fake_generate(target: Path) -> str:
        target.write_text("# public key: age1" + "a" * 58 + "\nAGE-SECRET-KEY-TEST\n", encoding="utf-8")
        return "age1" + "a" * 58

    monkeypatch.setattr(server_setup, "generate_identity", fake_generate)
    recovery_key = tmp_path / "recovery-read-key"
    monkeypatch.setattr(
        server_setup,
        "_ensure_recovery_ssh_key",
        lambda target: "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIRecoveryKey= recovery",
    )
    configured_profiles = []
    monkeypatch.setattr(
        server_setup,
        "_configure_local_recovery_profile",
        lambda **kwargs: configured_profiles.append(kwargs) or tmp_path / "profile.json",
    )
    monkeypatch.setattr(server_setup.os, "geteuid", lambda: 0)

    def fake_run(command, **_kwargs):
        result_path = Path(command[command.index("--result") + 1])
        result_path.write_text(
            json.dumps(
                {
                    "host": "backup.example.net",
                    "port": 22,
                    "username": "rbf-backup",
                    "recovery_username": "rbf-recovery",
                    "remote_directory": "/data",
                    "host_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBackupHostKey=",
                    "host_key_fingerprint": "SHA256:" + "A" * 43,
                    "managed_server": True,
                }
            ),
            encoding="utf-8",
        )

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(server_setup.subprocess, "run", fake_run)
    result = server_setup.provision_backup_server(
        request,
        host="backup.example.net",
        output=output,
        identity=identity,
        recovery_ssh_key=recovery_key,
    )
    payload = json.loads(result.read_text(encoding="utf-8"))
    assert payload["kind"] == "rbf-backup-enrollment-response"
    assert payload["age_recipient"].startswith("age1")
    assert "AGE-SECRET" not in result.read_text(encoding="utf-8")
    assert "AGE-SECRET" in identity.read_text(encoding="utf-8")
    assert configured_profiles[0]["username"] == "rbf-recovery"
    assert configured_profiles[0]["ssh_key"] == recovery_key.resolve()


def test_server_provisioning_can_skip_local_recovery_profile(tmp_path, monkeypatch) -> None:
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "kind": "rbf-backup-enrollment-request",
                "enrollment_id": "B" * 32,
                "ssh_public_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIProductKey= product",
                "requested_username": "rbf-backup",
                "requested_directory": "/data",
            }
        ),
        encoding="utf-8",
    )
    identity = tmp_path / "identity.txt"
    identity.write_text("# public key: age1" + "b" * 58 + "\nSECRET\n", encoding="utf-8")
    provisioner = tmp_path / "Provision-RbfBackupServer.sh"
    provisioner.write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setattr(server_setup, "support_script", lambda *_args, **_kwargs: provisioner)
    monkeypatch.setattr(server_setup, "_ensure_recovery_ssh_key", lambda _path: "ssh-ed25519 AAAA recovery")
    monkeypatch.setattr(
        server_setup,
        "_configure_local_recovery_profile",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("profile must not be configured")),
    )
    monkeypatch.setattr(server_setup.os, "geteuid", lambda: 0)

    def fake_run(command, **_kwargs):
        result_path = Path(command[command.index("--result") + 1])
        result_path.write_text(
            json.dumps(
                {
                    "host": "backup.example.net",
                    "port": 22,
                    "username": "rbf-backup",
                    "recovery_username": "rbf-recovery",
                    "remote_directory": "/data",
                    "host_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBackupHostKey=",
                    "host_key_fingerprint": "SHA256:" + "C" * 43,
                }
            ),
            encoding="utf-8",
        )
        return type("Result", (), {"returncode": 0})()

    monkeypatch.setattr(server_setup.subprocess, "run", fake_run)
    output = tmp_path / "response.json"
    server_setup.provision_backup_server(
        request,
        host="backup.example.net",
        output=output,
        identity=identity,
        recovery_ssh_key=tmp_path / "recovery-key",
        configure_local_profile=False,
    )
    assert output.is_file()


def test_recovery_read_key_is_created_once_with_private_permissions(tmp_path) -> None:
    import shutil
    import pytest
    if not shutil.which("ssh-keygen"):
        pytest.skip("ssh-keygen is not available in the test environment")
    key = tmp_path / "recovery-readonly"
    first = server_setup._ensure_recovery_ssh_key(key)
    first_bytes = key.read_bytes()
    second = server_setup._ensure_recovery_ssh_key(key)
    assert first == second
    assert key.read_bytes() == first_bytes
    assert key.stat().st_mode & 0o077 == 0
    assert first.startswith("ssh-ed25519 ")


def test_enrollment_request_loader_accepts_bom_and_reports_actionable_paths(tmp_path) -> None:
    import pytest

    missing = tmp_path / "missing.json"
    with pytest.raises(RuntimeError, match="nicht gefunden") as missing_error:
        server_setup._load_request(missing)
    assert str(missing.resolve()) in str(missing_error.value)

    invalid = tmp_path / "invalid.json"
    invalid.write_text("{broken", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Zeile 1"):
        server_setup._load_request(invalid)

    valid = tmp_path / "request.json"
    valid.write_text(
        "\ufeff" + json.dumps(
            {
                "schema_version": 1,
                "kind": "rbf-backup-enrollment-request",
                "enrollment_id": "C" * 32,
                "ssh_public_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIProductKey= product",
                "requested_username": "rbf-backup",
                "requested_directory": "/data",
            }
        ),
        encoding="utf-8",
    )
    assert server_setup._load_request(valid)["enrollment_id"] == "C" * 32


def test_server_provisioning_rejects_cli_user_that_differs_from_request(tmp_path, monkeypatch) -> None:
    import pytest

    request = tmp_path / "request.json"
    request.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "kind": "rbf-backup-enrollment-request",
                "enrollment_id": "D" * 32,
                "ssh_public_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIProductKey= product",
                "requested_username": "rbf-backup",
                "requested_directory": "/data",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        server_setup,
        "generate_identity",
        lambda target: (_ for _ in ()).throw(AssertionError("must fail before generating keys")),
    )
    with pytest.raises(RuntimeError, match="stimmt nicht mit der Enrollment-Anfrage"):
        server_setup.provision_backup_server(
            request,
            host="backup.example.net",
            output=tmp_path / "response.json",
            identity=tmp_path / "identity.txt",
            username="other-backup",
        )


def test_server_cli_prints_copy_safe_next_steps(tmp_path, monkeypatch, capsys) -> None:
    from rbf_recovery_tool import cli

    request = tmp_path / "request.json"
    request.write_text("{}", encoding="utf-8")
    response = tmp_path / "response.json"

    def fake_provision(_request, **kwargs):
        output = Path(kwargs["output"])
        output.write_text(
            json.dumps(
                {
                    "host_key_fingerprint": "SHA256:" + "A" * 43,
                }
            ),
            encoding="utf-8",
        )
        return output

    monkeypatch.setattr(cli, "provision_backup_server", fake_provision)
    monkeypatch.setattr(cli, "profile_path", lambda: tmp_path / "profile.json")
    result = cli.main(
        [
            "server",
            "provision",
            str(request),
            "--host",
            "192.168.2.107",
            "--output",
            str(response),
            "--identity",
            str(tmp_path / "identity.txt"),
            "--recovery-key",
            str(tmp_path / "recovery-key"),
        ]
    )
    output = capsys.readouterr().out
    assert result == 0
    assert "FERTIG: Der Backup-Server wurde provisioniert." in output
    assert str(response) in output
    assert "Antwort importieren und prüfen" in output
    assert "rbf-recovery-tool pull" in output


def test_linux_provisioner_keeps_key_only_accounts_ssh_accessible() -> None:
    script = (
        Path(__file__).resolve().parents[2]
        / "linux"
        / "recovery-tool"
        / "Provision-RbfBackupServer.sh"
    ).read_text(encoding="utf-8")
    assert 'passwd -l "$USERNAME"' not in script
    assert 'passwd -l "$RECOVERY_USERNAME"' not in script
    assert 'set_unknown_password "$USERNAME"' in script
    assert 'set_unknown_password "$RECOVERY_USERNAME"' in script
    assert "PasswordAuthentication no" in script
    assert "KbdInteractiveAuthentication no" in script
