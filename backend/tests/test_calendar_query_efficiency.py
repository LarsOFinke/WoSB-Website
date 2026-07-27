from datetime import datetime, timedelta
from types import SimpleNamespace

from app.modules.calendar.services import fleet_event_service
from app.modules.fleet.services.fleet_service import can_manage_fleet


class _ScalarResult:
    def __init__(self, rows):
        self._rows = rows

    def unique(self):
        return self

    def all(self):
        return self._rows


class _CalendarSession:
    def __init__(self, rows):
        self.rows = rows
        self.list_queries = 0

    def scalars(self, statement):
        self.list_queries += 1
        return _ScalarResult(self.rows)


def _event(event_id: int, squad_id: int | None):
    starts_at = datetime(2026, 7, 18, 18, 0) + timedelta(hours=event_id)
    squad = (
        None
        if squad_id is None
        else SimpleNamespace(id=squad_id, name=f"Squad {squad_id}", slug=f"squad-{squad_id}")
    )
    return SimpleNamespace(
        id=event_id,
        title=f"Event {event_id}",
        category="training",
        description=None,
        location=None,
        start_at=starts_at,
        end_at=starts_at + timedelta(hours=1),
        all_day=False,
        owner_id=1,
        owner=SimpleNamespace(
            id=1,
            username="captain",
            display_name="Captain",
            role="user",
            is_active=True,
            created_at=starts_at,
        ),
        squad_id=squad_id,
        squad=squad,
        is_cancelled=False,
        created_at=starts_at,
        updated_at=starts_at,
    )


def test_calendar_list_resolves_management_permissions_once(monkeypatch) -> None:
    calls = {"fleet": 0, "visible": 0, "managed": 0}

    def fleet_access(db, user):
        calls["fleet"] += 1
        return False

    def visible_squads(db, user):
        calls["visible"] += 1
        return [10, 20]

    def managed_squads(db, user):
        calls["managed"] += 1
        return [10]

    monkeypatch.setattr(fleet_event_service, "can_manage_fleet", fleet_access)
    monkeypatch.setattr(fleet_event_service, "user_squad_ids", visible_squads)
    monkeypatch.setattr(fleet_event_service, "user_managed_squad_ids", managed_squads)
    monkeypatch.setattr(
        fleet_event_service,
        "_can_manage_scope",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("per-event query")),
    )

    db = _CalendarSession([_event(1, None), _event(2, 10), _event(3, 20)])
    rows = fleet_event_service.list_fleet_events(db, SimpleNamespace(id=1))

    assert db.list_queries == 1
    assert calls == {"fleet": 1, "visible": 1, "managed": 1}
    assert [row.can_manage for row in rows] == [False, True, False]


def test_fleet_management_check_does_not_load_fleet_summaries() -> None:
    class PermissionSession:
        def __init__(self):
            self.results = iter([7, 99])
            self.queries = 0

        def scalar(self, statement):
            self.queries += 1
            return next(self.results)

    db = PermissionSession()
    user = SimpleNamespace(id=42, can_moderate=False)

    assert can_manage_fleet(db, user, fleet_id=7)
    assert db.queries == 2
