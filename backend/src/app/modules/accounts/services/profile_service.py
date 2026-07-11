from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounts.models.user import User
from app.modules.accounts.models.user_profile import UserProfileRolePreference, UserProfileShipPreference
from app.modules.accounts.schemas.profile_update import ProfileUpdate
from app.modules.fleet.services.fleet_service import sync_user_primary_fleet
from app.modules.permissions.models.role import FleetRoleDefinition
from app.modules.ships.models.ship import Ship


class ProfileValidationError(ValueError):
    pass


def _validate_ids(db: Session, payload: ProfileUpdate) -> None:
    ship_ids = set(db.scalars(select(Ship.id).where(Ship.id.in_(payload.preferred_ship_ids), Ship.is_active.is_(True))).all())
    role_ids = set(db.scalars(select(FleetRoleDefinition.id).where(FleetRoleDefinition.id.in_(payload.preferred_role_ids))).all())
    if ship_ids != set(payload.preferred_ship_ids):
        raise ProfileValidationError("One or more preferred ships are invalid.")
    if role_ids != set(payload.preferred_role_ids):
        raise ProfileValidationError("One or more preferred roles are invalid.")


def update_profile(db: Session, user: User, payload: ProfileUpdate) -> User:
    """Update user-owned profile data and normalized preferences."""

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
    profile.ship_preferences = [
        UserProfileShipPreference(ship_id=ship_id, sort_order=index * 10)
        for index, ship_id in enumerate(payload.preferred_ship_ids, start=1)
    ]
    profile.role_preferences = [
        UserProfileRolePreference(fleet_role_id=role_id, sort_order=index * 10)
        for index, role_id in enumerate(payload.preferred_role_ids, start=1)
    ]
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
