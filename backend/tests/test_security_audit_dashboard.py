from datetime import timedelta
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.base import Base
from app.modules.admin.models.security_event import (
    SECURITY_SIGNAL_LOGIN_FAILURE,
    SECURITY_SIGNAL_RATE_LIMIT,
    SECURITY_SIGNAL_RECONNAISSANCE,
    SecuritySignalBucket,
)
from app.modules.admin.services.audit_log_service import list_audit_logs, record_audit
from app.modules.admin.services.security_dashboard_service import build_security_dashboard
from app.modules.registry import register_all_models


def isolated_session():
    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine, expire_on_commit=False)


def test_security_dashboard_scores_only_coarse_ban_signals() -> None:
    with isolated_session() as db:
        today = utc_now().date()
        db.add_all(
            [
                SecuritySignalBucket(
                    day=today,
                    signal=SECURITY_SIGNAL_LOGIN_FAILURE,
                    client_ip="10.0.0.1",
                    event_count=1,
                ),
                SecuritySignalBucket(
                    day=today,
                    signal=SECURITY_SIGNAL_RECONNAISSANCE,
                    client_ip="198.51.100.44",
                    event_count=2,
                ),
            ]
        )
        db.commit()

        dashboard = build_security_dashboard(db, from_date=today, to_date=today)

        assert dashboard.total_events == 3
        assert dashboard.unique_ips == 2
        assert dashboard.signal_counts[SECURITY_SIGNAL_RECONNAISSANCE] == 2
        assert dashboard.ips[0].client_ip == "198.51.100.44"
        assert dashboard.ips[0].reconnaissance == 2
        assert dashboard.ips[0].reconnaissance_points == 50
        assert dashboard.ips[0].login_failure_points == 0
        assert dashboard.ips[0].volume_bonus == 0
        assert dashboard.ips[0].threat_level == "elevated"
        assert dashboard.ips[1].login_failures == 1
        assert not hasattr(dashboard.ips[0], "top_paths")
        assert not hasattr(dashboard.ips[0], "user_agent")


def test_security_dashboard_combines_date_threat_and_ip_filters() -> None:
    with isolated_session() as db:
        today = utc_now().date()
        yesterday = today - timedelta(days=1)
        db.add_all(
            [
                SecuritySignalBucket(
                    day=yesterday,
                    signal=SECURITY_SIGNAL_LOGIN_FAILURE,
                    client_ip="10.0.0.1",
                    event_count=1,
                ),
                SecuritySignalBucket(
                    day=today,
                    signal=SECURITY_SIGNAL_RECONNAISSANCE,
                    client_ip="198.51.100.44",
                    event_count=2,
                ),
                SecuritySignalBucket(
                    day=today,
                    signal=SECURITY_SIGNAL_RATE_LIMIT,
                    client_ip="203.0.113.7",
                    event_count=1,
                ),
            ]
        )
        db.commit()

        dashboard = build_security_dashboard(
            db,
            from_date=yesterday,
            to_date=today,
            threat_level="elevated",
            client_ip="198.51.100.44",
        )
        assert dashboard.unique_ips == 1
        assert dashboard.total_events == 2
        assert [row.client_ip for row in dashboard.ips] == ["198.51.100.44"]
        assert dashboard.days[0].total_events == 0
        assert dashboard.days[1].total_events == 2


def test_audit_log_records_actor_action_and_changed_field_names() -> None:
    with isolated_session() as db:
        actor = SimpleNamespace(id=None, username="moderator", role="moderator")
        record_audit(
            db,
            actor=actor,
            entity_type="build",
            entity_id=42,
            action="update",
            summary="Build updated.",
            changed_fields=["details", "upgrade_1", "details"],
        )

        rows = list_audit_logs(db, entity_type="build", actor="moder")
        assert len(rows) == 1
        assert rows[0].actor_username == "moderator"
        assert rows[0].action == "update"
        assert rows[0].entity_id == "42"
        assert rows[0].changed_fields == ["details", "upgrade_1"]
