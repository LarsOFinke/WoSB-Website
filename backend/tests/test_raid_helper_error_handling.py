from __future__ import annotations

from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.registry import register_all_models
from app.modules.raid_helper.schemas.raid_helper import RaidHelperProfileCreate
from app.modules.raid_helper.services import raid_helper_configuration as service
from app.modules.raid_helper.services.errors import RaidHelperError


register_all_models()


class FailingSession:
    def __init__(self, exc: Exception) -> None:
        self.exc = exc
        self.rolled_back = False

    def add(self, _row) -> None:
        return None

    def commit(self) -> None:
        raise self.exc

    def rollback(self) -> None:
        self.rolled_back = True


def _payload() -> RaidHelperProfileCreate:
    return RaidHelperProfileCreate(
        name="Primary",
        server_id="12345",
        api_key="abcdefgh",
    )


def test_unexpected_raid_helper_database_failures_are_not_reported_as_duplicates(monkeypatch) -> None:
    monkeypatch.setattr(service, "webhook_secret_box", SimpleNamespace(encrypt=lambda value: f"encrypted:{value}"))
    db = FailingSession(RuntimeError("database unavailable"))

    with pytest.raises(RuntimeError, match="database unavailable"):
        service.create_profile(db, _payload(), SimpleNamespace(username="captain"))
    assert db.rolled_back is True


def test_raid_helper_integrity_errors_are_mapped_to_duplicate_messages(monkeypatch) -> None:
    monkeypatch.setattr(service, "webhook_secret_box", SimpleNamespace(encrypt=lambda value: f"encrypted:{value}"))
    db = FailingSession(IntegrityError("insert", {}, RuntimeError("unique")))

    with pytest.raises(RaidHelperError, match="already exists"):
        service.create_profile(db, _payload(), SimpleNamespace(username="captain"))
    assert db.rolled_back is True
