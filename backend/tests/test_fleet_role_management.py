from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.modules.accounts.services.auth_service import create_user
from app.modules.fleet.models.fleet import Fleet
from app.modules.fleet.schemas.fleet_role import FleetRoleCreate, FleetRoleUpdate
from app.modules.fleet.services.fleet_role_service import (
    FleetRolePermissionError,
    FleetRoleValidationError,
    create_fleet_role,
    delete_fleet_role,
    list_fleet_roles,
    update_fleet_role,
)
from app.modules.fleet.services.fleet_service import assign_fleet_role
from app.modules.registry import register_all_models


def test_fleet_admiral_can_manage_custom_roles_but_system_roles_stay_protected() -> None:
    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        fleet = Fleet(name="Role Fleet", slug="royal-blackwater-fleet", focus="mixed", sort_order=10)
        db.add(fleet)
        db.flush()
        admiral = create_user(db, username="role-admiral", password="FleetRoleAdmiral123!", display_name="Role Admiral")
        lieutenant = create_user(db, username="role-lieutenant", password="FleetRoleLieutenant123!", display_name="Role Lieutenant")
        assign_fleet_role(db, fleet.id, admiral.id, "fleet_admiral")
        assign_fleet_role(db, fleet.id, lieutenant.id, "fleet_lieutenant")

        created = create_fleet_role(
            db,
            fleet.id,
            FleetRoleCreate(
                code="quartermaster",
                label="Quartermaster",
                rank=45,
                is_leadership=True,
                can_manage_members=True,
            ),
            admiral,
        )
        assert created.code == "quartermaster"
        assert created.is_system is False
        assert created.can_manage_members is True

        updated = update_fleet_role(
            db,
            fleet.id,
            created.id,
            FleetRoleUpdate(label="Fleet Quartermaster", rank=46),
            admiral,
        )
        assert updated.label == "Fleet Quartermaster"
        assert any(role.code == "quartermaster" for role in list_fleet_roles(db))

        try:
            create_fleet_role(
                db,
                fleet.id,
                FleetRoleCreate(code="denied", label="Denied", rank=20),
                lieutenant,
            )
        except FleetRolePermissionError:
            pass
        else:
            raise AssertionError("Only administrators and fleet admirals may manage fleet roles.")

        system_role = next(role for role in list_fleet_roles(db) if role.code == "fleet_admiral")
        try:
            update_fleet_role(db, fleet.id, system_role.id, FleetRoleUpdate(label="Changed"), admiral)
        except FleetRoleValidationError:
            pass
        else:
            raise AssertionError("System fleet roles must remain immutable.")

        assert delete_fleet_role(db, fleet.id, created.id, admiral) is True
