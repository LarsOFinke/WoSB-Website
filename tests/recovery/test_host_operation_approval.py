from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


MODULE_PATH = Path(__file__).parents[2] / "infrastructure/scripts/services/host-operation-approval.py"
SPEC = importlib.util.spec_from_file_location("host_operation_approval", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


def root_owned_fstat(monkeypatch):
    original = MODULE.os.fstat

    def wrapped(descriptor):
        value = original(descriptor)
        return SimpleNamespace(
            st_mode=value.st_mode, st_uid=0, st_size=value.st_size,
        )

    monkeypatch.setattr(MODULE.os, "fstat", wrapped)


def test_approval_is_operation_bound_single_use(tmp_path, monkeypatch, capsys):
    MODULE.arm(tmp_path, "backup", 10)
    token = capsys.readouterr().out.splitlines()[0]
    root_owned_fstat(monkeypatch)
    MODULE.consume(tmp_path, "backup", hashlib.sha256(token.encode()).hexdigest())
    assert not MODULE.approval_path(tmp_path, "backup").exists()
    with pytest.raises(FileNotFoundError):
        MODULE.consume(tmp_path, "backup", hashlib.sha256(token.encode()).hexdigest())


def test_wrong_hash_fails_and_consumes_attempt(tmp_path, monkeypatch, capsys):
    MODULE.arm(tmp_path, "restart", 10)
    capsys.readouterr()
    root_owned_fstat(monkeypatch)
    with pytest.raises(SystemExit, match="invalid, expired"):
        MODULE.consume(tmp_path, "restart", "0" * 64)
    assert not MODULE.approval_path(tmp_path, "restart").exists()


def test_unknown_operation_cannot_be_armed(tmp_path):
    with pytest.raises(SystemExit, match="Unsupported"):
        MODULE.arm(tmp_path, "shell", 10)
