from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.db.session import SessionLocal
from app.modules.accounts.models.user import User
from app.modules.accounts.services.auth_service import create_user
from app.modules.fleet.models.fleet import Fleet
from app.modules.fleet.models.fleet_membership import FleetMembership
from app.modules.fleet.services.fleet_service import join_fleet
from app.modules.fleet.schemas.fleet_join_request import FleetJoinRequest
from app.modules.permissions.models.role import FleetRoleDefinition
from app.modules.ships.models.ship import Ship
from app.bootstrap.manager import SeedManager
from main import app


def test_profile_is_single_source_for_fleet_directory_details() -> None:
    username = "profile-directory-source"
    password = "ProfileDirectory123!"
    with TestClient(app) as client:
        with SessionLocal() as db:
            seed_manager = SeedManager(db)
            seed_manager.seed_role_catalog()
            seed_manager.seed_fleets()
            seed_manager.seed_weapon_slot_types()
            seed_manager.seed_ships()

            user = db.query(User).filter(User.username == username).one_or_none()
            if user is None:
                user = create_user(db, username=username, password=password, display_name="Directory Source", role="user")
            fleet = db.query(Fleet).order_by(Fleet.id).first()
            ship = db.query(Ship).filter(Ship.is_active.is_(True)).order_by(Ship.id).first()
            role = db.query(FleetRoleDefinition).order_by(FleetRoleDefinition.rank).first()
            assert fleet and ship and role
            membership = join_fleet(db, user, FleetJoinRequest(fleet_id=fleet.id, note="Profile-backed application"))
            membership_id = membership.id
            ship_id = ship.id
            role_id = role.id

        login = client.post("/api/auth/login", json={"username": username, "password": password})
        assert login.status_code == 200, login.text
        response = client.put("/api/profile", json={
            "display_name": "Directory Source",
            "preferred_focus": "pvp_general",
            "availability": "Weekday evenings",
            "timezone": "Europe/Berlin",
            "discord_handle": "captain.blackwater",
            "preferred_ship_ids": [ship_id],
            "preferred_role_ids": [role_id],
            "note": "Optional public profile note",
        })
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["availability"] == "Weekday evenings"
        assert body["preferred_ship_ids"] == [ship_id]

        # Editing only the free-form profile note must reuse the existing
        # normalized preference rows instead of violating their unique keys.
        note_update = client.put("/api/profile", json={
            "display_name": "Directory Source",
            "preferred_focus": "pvp_general",
            "availability": "Weekday evenings",
            "timezone": "Europe/Berlin",
            "discord_handle": "captain.blackwater",
            "preferred_ship_ids": [ship_id],
            "preferred_role_ids": [role_id],
            "note": "Updated public profile note",
        })
        assert note_update.status_code == 200, note_update.text
        assert note_update.json()["note"] == "Updated public profile note"
        assert note_update.json()["preferred_ship_ids"] == [ship_id]
        assert note_update.json()["preferred_role_ids"] == [role_id]

        with SessionLocal() as db:
            columns = {column["name"] for column in inspect(db.bind).get_columns("fleet_memberships")}
            assert {"availability", "timezone", "discord_handle", "preferred_ships"}.isdisjoint(columns)
            membership = db.get(FleetMembership, membership_id)
            assert membership is not None
            assert membership.availability == "Weekday evenings"
            assert membership.timezone == "Europe/Berlin"
            assert membership.discord_handle == "captain.blackwater"
            assert membership.preferred_ships
            assert membership.preferred_roles
