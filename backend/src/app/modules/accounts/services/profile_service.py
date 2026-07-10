from sqlalchemy.orm import Session

from app.modules.accounts.models.user import User
from app.modules.accounts.schemas.profile_update import ProfileUpdate
from app.modules.fleet.services.fleet_service import sync_user_primary_fleet


def update_profile(db: Session, user: User, payload: ProfileUpdate) -> User:
    """Update public profile fields while keeping official fleet data centralized.

    Free-text fleet data remains available only for users who are not connected
    to the official fleet. Official fleet display is derived from the
    active normalized ``fleet_memberships`` relation.
    """

    user.display_name = payload.display_name
    sync_user_primary_fleet(db, user)
    if user.fleet_id is None:
        user.fleet_name = payload.fleet_name
    user.preferred_focus = payload.preferred_focus
    user.note = payload.note
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
