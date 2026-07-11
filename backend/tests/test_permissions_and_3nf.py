from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from app.db.base import Base
from app.modules.accounts.services.auth_service import create_user
from app.modules.admin.schemas.user_administration import UserAdministrationUpdate
from app.modules.admin.services.user_administration_service import UserAdministrationError, update_user_account
from app.modules.registry import register_all_models


def _db() -> Session:
    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_role_hierarchy_protects_administrators_and_allows_lower_account_management() -> None:
    with _db() as db:
        admin = create_user(db, username="hierarchy-admin", password="test-password-123", display_name="Admin", role="admin")
        peer = create_user(db, username="hierarchy-peer", password="test-password-123", display_name="Peer", role="admin")
        moderator = create_user(db, username="hierarchy-moderator", password="test-password-123", display_name="Mod", role="moderator")
        member = create_user(db, username="hierarchy-member", password="test-password-123", display_name="Member", role="user")

        for actor, target in ((moderator, admin), (admin, peer)):
            try:
                update_user_account(db, actor=actor, target_id=target.id, payload=UserAdministrationUpdate(is_active=False))
            except UserAdministrationError:
                pass
            else:
                raise AssertionError("Equal or lower authority must not deactivate an administrator.")

        updated = update_user_account(db, actor=admin, target_id=moderator.id, payload=UserAdministrationUpdate(is_active=False))
        assert updated.is_active is False
        promoted = update_user_account(db, actor=admin, target_id=member.id, payload=UserAdministrationUpdate(role="moderator"))
        assert promoted.role == "moderator"


def test_normalized_schema_has_no_transitive_role_or_compound_text_columns() -> None:
    with _db() as db:
        inspector = inspect(db.bind)
        def columns(table: str) -> set[str]:
            return {column["name"] for column in inspector.get_columns(table)}
        assert "role" not in columns("users")
        assert "role" not in columns("fleet_memberships")
        assert "preferred_ships" not in columns("fleet_memberships")
        assert {"availability", "timezone", "discord_handle"}.isdisjoint(columns("fleet_memberships"))
        assert {"availability", "timezone", "discord_handle"}.issubset(columns("user_profiles"))
        assert "role" not in columns("squad_members")
        assert "primary_fleet_membership_id" not in columns("user_profiles")
        assert "weapon_layout" not in columns("ships")
        assert "allowed_slot_types" not in columns("build_item_options")
        assert "weapon_weight_pounds" not in columns("build_item_options")
        assert "max_weapon_pounds" not in columns("ship_weapon_mounts")
        assert {
            "external_fleet_name",
            "fleet_id",
            "wants_fleet_membership",
            "fleet_application_note",
            "fleet_availability",
            "fleet_preferred_ships",
            "fleet_timezone",
            "fleet_discord_handle",
        }.isdisjoint(columns("registration_requests"))
        for table in (
            "site_roles",
            "fleet_roles",
            "squad_roles",
            "user_profile_ship_preferences",
            "user_profile_role_preferences",
            "weapon_classes",
            "weapon_slot_types",
            "ship_weapon_mounts",
            "build_item_option_slot_types",
        ):
            assert table in inspector.get_table_names()


def test_normalized_fleet_roles_drive_public_leadership_order() -> None:
    from app.modules.fleet.models.fleet import Fleet, FLEET_MEMBER_ACTIVE
    from app.modules.fleet.models.fleet_membership import FleetMembership
    from app.modules.fleet.services.fleet_service import get_primary_fleet
    from app.modules.permissions.services.role_service import assign_fleet_role_definition

    with _db() as db:
        fleet = Fleet(
            name="Royal Blackwater Fleet",
            slug="royal-blackwater-fleet",
            focus="mixed",
            sort_order=10,
            is_active=True,
        )
        db.add(fleet)
        db.flush()
        admiral = create_user(db, username="fleet-admiral", password="test-password-123", display_name="Admiral", role="user")
        lieutenant = create_user(db, username="fleet-lieutenant", password="test-password-123", display_name="Lieutenant", role="user")
        member = create_user(db, username="fleet-member", password="test-password-123", display_name="Member", role="user")
        rows = []
        for user, role in ((admiral, "fleet_admiral"), (lieutenant, "fleet_lieutenant"), (member, "member")):
            membership = FleetMembership(fleet_id=fleet.id, user_id=user.id, status=FLEET_MEMBER_ACTIVE)
            assign_fleet_role_definition(db, membership, role)
            db.add(membership)
            rows.append(membership)
        db.commit()

        loaded = get_primary_fleet(db, include_members=True)
        assert loaded is not None
        assert [(row.user.display_name, row.role) for row in loaded.leaders] == [
            ("Admiral", "fleet_admiral"),
            ("Lieutenant", "fleet_lieutenant"),
        ]
