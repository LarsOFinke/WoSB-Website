from datetime import datetime, timedelta
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.core.time import utc_now
from app.modules.admin.models.app_log import AppLog
from app.modules.admin.services.audit_log_service import list_audit_logs, record_audit
from app.modules.admin.services.security_dashboard_service import build_security_dashboard
from app.modules.registry import register_all_models


def isolated_session():
    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine, expire_on_commit=False)


def test_security_dashboard_scores_suspicious_probe_ip_above_normal_traffic() -> None:
    with isolated_session() as db:
        now = utc_now()
        db.add_all([
            AppLog(created_at=now - timedelta(hours=2), level="INFO", logger="request", message="ok", path="/api/builds", status_code=200, client_ip="10.0.0.1"),
            AppLog(created_at=now - timedelta(hours=1), level="INFO", logger="request", message="probe", path="/api/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php", status_code=404, client_ip="198.51.100.44"),
            AppLog(created_at=now, level="ERROR", logger="request", message="probe", path="/.env", status_code=500, client_ip="198.51.100.44"),
        ])
        db.commit()

        dashboard = build_security_dashboard(db, from_date=now.date(), to_date=now.date())

        assert dashboard.total_requests == 3
        assert dashboard.unique_ips == 2
        assert dashboard.suspicious_hits == 2
        assert dashboard.ips[0].client_ip == "198.51.100.44"
        assert dashboard.ips[0].threat_score > dashboard.ips[1].threat_score
        assert dashboard.ips[0].threat_level in {"elevated", "critical"}


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
