from __future__ import annotations

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.modules.accounts.services.auth_service import create_user
from app.modules.fleet.models.fleet import Fleet
from app.modules.fleet.services.fleet_service import assign_fleet_role
from main import app


def _login(client: TestClient, username: str, password: str) -> None:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text


def _logout(client: TestClient) -> None:
    response = client.post("/api/auth/logout")
    assert response.status_code == 204, response.text


def _official_fleet(db) -> Fleet:
    fleet = db.query(Fleet).order_by(Fleet.id).first()
    if fleet is None:
        fleet = Fleet(
            name="Royal Blackwater Fleet",
            slug="royal-blackwater-fleet",
            focus="mixed",
            description="Hierarchy fixture",
            standing_orders="Respect the chain of command.",
            sort_order=10,
        )
        db.add(fleet)
        db.commit()
        db.refresh(fleet)
    return fleet


def test_membership_hierarchy_protects_staff_and_fleet_command() -> None:
    passwords = {
        "admin": "HierarchyAdmin123!",
        "moderator": "HierarchyModerator123!",
        "peer": "HierarchyPeerModerator123!",
        "admiral": "HierarchyAdmiral123!",
        "lieutenant": "HierarchyLieutenant123!",
        "member": "HierarchyMember123!",
        "admin_peer": "HierarchyAdminPeer123!",
    }
    with TestClient(app) as client:
        with SessionLocal() as db:
            fleet = _official_fleet(db)
            admin = create_user(db, username="fleet-hierarchy-admin", password=passwords["admin"], display_name="Hierarchy Admin", role="admin")
            moderator = create_user(db, username="fleet-hierarchy-moderator", password=passwords["moderator"], display_name="Hierarchy Moderator", role="moderator")
            peer = create_user(db, username="fleet-hierarchy-peer", password=passwords["peer"], display_name="Peer Moderator", role="moderator")
            admiral = create_user(db, username="fleet-hierarchy-admiral", password=passwords["admiral"], display_name="Protected Admiral", role="user")
            lieutenant = create_user(db, username="fleet-hierarchy-lieutenant", password=passwords["lieutenant"], display_name="Fleet Lieutenant", role="user")
            member = create_user(db, username="fleet-hierarchy-member", password=passwords["member"], display_name="Fleet Member", role="user")
            admin_peer = create_user(db, username="fleet-hierarchy-admin-peer", password=passwords["admin_peer"], display_name="Hierarchy Admin Peer", role="admin")

            memberships = {
                "admin": assign_fleet_role(db, fleet.id, admin.id, "member"),
                "moderator": assign_fleet_role(db, fleet.id, moderator.id, "member"),
                "peer": assign_fleet_role(db, fleet.id, peer.id, "member"),
                "admiral": assign_fleet_role(db, fleet.id, admiral.id, "fleet_admiral"),
                "lieutenant": assign_fleet_role(db, fleet.id, lieutenant.id, "fleet_lieutenant"),
                "member": assign_fleet_role(db, fleet.id, member.id, "member"),
                "admin_peer": assign_fleet_role(db, fleet.id, admin_peer.id, "member"),
            }
            fleet_id = fleet.id
            membership_ids = {key: value.id for key, value in memberships.items()}

        _login(client, moderator.username, passwords["moderator"])
        detail = client.get(f"/api/fleets/{fleet_id}/manage")
        assert detail.status_code == 200, detail.text
        rows = {row["user"]["username"]: row for row in detail.json()["memberships"]}
        assert rows[peer.username]["management"]["reason"] == "site_peer"
        assert rows[admin.username]["management"]["reason"] == "site_admin"
        assert rows[admiral.username]["management"]["reason"] == "fleet_admiral"
        assert rows[lieutenant.username]["management"]["can_change_status"] is True
        assert rows[lieutenant.username]["management"]["assignable_roles"] == ["member", "fleet_lieutenant"]

        for target in ("peer", "admin", "admiral"):
            response = client.put(
                f"/api/fleets/{fleet_id}/memberships/{membership_ids[target]}",
                json={"status": "inactive"},
            )
            assert response.status_code == 403, response.text

        forbidden_promotion = client.put(
            f"/api/fleets/{fleet_id}/memberships/{membership_ids['member']}",
            json={"role": "fleet_admiral"},
        )
        assert forbidden_promotion.status_code == 403, forbidden_promotion.text

        allowed_promotion = client.put(
            f"/api/fleets/{fleet_id}/memberships/{membership_ids['member']}",
            json={"role": "fleet_lieutenant"},
        )
        assert allowed_promotion.status_code == 200, allowed_promotion.text
        _logout(client)

        _login(client, lieutenant.username, passwords["lieutenant"])
        peer_lieutenant = client.put(
            f"/api/fleets/{fleet_id}/memberships/{membership_ids['member']}",
            json={"status": "inactive"},
        )
        assert peer_lieutenant.status_code == 403, peer_lieutenant.text
        _logout(client)

        _login(client, admin.username, passwords["admin"])
        admin_detail = client.get(f"/api/fleets/{fleet_id}/manage")
        assert admin_detail.status_code == 200, admin_detail.text
        admin_rows = {row["user"]["username"]: row for row in admin_detail.json()["memberships"]}
        assert admin_rows[admin.username]["management"]["can_edit_directory"] is True
        assert admin_rows[admin.username]["management"]["reason"] is None
        assert admin_rows[admin_peer.username]["management"]["can_change_status"] is True

        self_edit = client.put(
            f"/api/fleets/{fleet_id}/memberships/{membership_ids['admin']}",
            json={"assignment": "Command administration"},
        )
        assert self_edit.status_code == 200, self_edit.text

        self_role_change = client.put(
            f"/api/fleets/{fleet_id}/memberships/{membership_ids['admin']}",
            json={"role": "fleet_lieutenant"},
        )
        assert self_role_change.status_code == 200, self_role_change.text

        self_status_change = client.put(
            f"/api/fleets/{fleet_id}/memberships/{membership_ids['admin']}",
            json={"status": "inactive"},
        )
        assert self_status_change.status_code == 200, self_status_change.text

        self_reactivation = client.put(
            f"/api/fleets/{fleet_id}/memberships/{membership_ids['admin']}",
            json={"status": "active"},
        )
        assert self_reactivation.status_code == 200, self_reactivation.text

        peer_admin_edit = client.put(
            f"/api/fleets/{fleet_id}/memberships/{membership_ids['admin_peer']}",
            json={"assignment": "Peer command administration"},
        )
        assert peer_admin_edit.status_code == 200, peer_admin_edit.text

        admin_edit = client.put(
            f"/api/fleets/{fleet_id}/memberships/{membership_ids['admiral']}",
            json={"assignment": "Protected command"},
        )
        assert admin_edit.status_code == 200, admin_edit.text


def test_last_active_admiral_is_protected_even_from_destructive_admin_actions() -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.db.base import Base
    from app.modules.fleet.models.fleet_membership import FleetMembership
    from app.modules.fleet.schemas.fleet_membership_update import FleetMembershipUpdate
    from app.modules.fleet.services.fleet_management_policy import FleetMembershipPermissionError
    from app.modules.fleet.services.fleet_service import update_membership
    from app.modules.permissions.services.role_service import assign_fleet_role_definition
    from app.modules.registry import register_all_models

    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        fleet = Fleet(
            name="Hierarchy Test Fleet",
            slug="royal-blackwater-fleet",
            focus="mixed",
            sort_order=10,
        )
        db.add(fleet)
        db.flush()
        admin = create_user(db, username="last-admiral-admin", password="test-password-123", display_name="Admin", role="admin")
        admiral = create_user(db, username="last-admiral-user", password="test-password-123", display_name="Admiral", role="user")
        membership = FleetMembership(fleet_id=fleet.id, user_id=admiral.id, status="active")
        assign_fleet_role_definition(db, membership, "fleet_admiral")
        db.add(membership)
        db.commit()

        try:
            update_membership(
                db,
                membership.id,
                FleetMembershipUpdate(status="inactive"),
                actor=admin,
            )
        except FleetMembershipPermissionError as exc:
            assert "last active fleet admiral" in str(exc).lower()
        else:
            raise AssertionError("The final active fleet admiral must remain protected.")
