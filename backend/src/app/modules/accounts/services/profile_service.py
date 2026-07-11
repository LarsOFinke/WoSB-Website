from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounts.models.user import User
from app.modules.accounts.models.user_profile import (
    UserProfile,
    UserProfileRolePreference,
    UserProfileShipPreference,
)
from app.modules.accounts.schemas.profile_update import ProfileUpdate
from app.modules.fleet.services.fleet_service import sync_user_primary_fleet
from app.modules.permissions.models.role import FleetRoleDefinition
from app.modules.ships.models.ship import Ship


class ProfileValidationError(ValueError):
    pass


def _validate_ids(db: Session, payload: ProfileUpdate) -> None:
    ship_ids = set(
        db.scalars(
            select(Ship.id).where(
                Ship.id.in_(payload.preferred_ship_ids),
                Ship.is_active.is_(True),
            )
        ).all()
    )
    role_ids = set(
        db.scalars(
            select(FleetRoleDefinition.id).where(
                FleetRoleDefinition.id.in_(payload.preferred_role_ids)
            )
        ).all()
    )
    if ship_ids != set(payload.preferred_ship_ids):
        raise ProfileValidationError("One or more preferred ships are invalid.")
    if role_ids != set(payload.preferred_role_ids):
        raise ProfileValidationError("One or more preferred roles are invalid.")


def _sync_ship_preferences(profile: UserProfile, ship_ids: list[int]) -> None:
    """Reuse existing rows so unchanged preferences never hit the unique key twice."""

    existing = {row.ship_id: row for row in profile.ship_preferences}
    synchronized: list[UserProfileShipPreference] = []
    for index, ship_id in enumerate(ship_ids, start=1):
        row = existing.pop(ship_id, None) or UserProfileShipPreference(ship_id=ship_id)
        row.sort_order = index * 10
        synchronized.append(row)
    profile.ship_preferences = synchronized


def _sync_role_preferences(profile: UserProfile, role_ids: list[int]) -> None:
    """Reuse existing rows so profile-only edits do not duplicate role links."""

    existing = {row.fleet_role_id: row for row in profile.role_preferences}
    synchronized: list[UserProfileRolePreference] = []
    for index, role_id in enumerate(role_ids, start=1):
        row = existing.pop(role_id, None) or UserProfileRolePreference(fleet_role_id=role_id)
        row.sort_order = index * 10
        synchronized.append(row)
    profile.role_preferences = synchronized


def update_profile(db: Session, user: User, payload: ProfileUpdate) -> User:
    """Update user-owned profile data and normalized preferences atomically."""

    _validate_ids(db, payload)
    user.display_name = payload.display_name
    sync_user_primary_fleet(db, user)
    if user.fleet_id is None:
        user.fleet_name = payload.fleet_name

    profile = user._ensure_profile()
    profile.preferred_focus = payload.preferred_focus
    profile.availability = payload.availability
    profile.timezone = payload.timezone
    profile.discord_handle = payload.discord_handle
    profile.note = payload.note
    _sync_ship_preferences(profile, payload.preferred_ship_ids)
    _sync_role_preferences(profile, payload.preferred_role_ids)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user
