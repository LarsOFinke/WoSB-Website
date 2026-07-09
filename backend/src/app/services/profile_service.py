from sqlalchemy.orm import Session

from app.models import User
from app.schemas import ProfileUpdate


def update_profile(db: Session, user: User, payload: ProfileUpdate) -> User:
    """Update public profile fields without touching account or fleet membership tables."""

    user.display_name = payload.display_name
    user.fleet_name = payload.fleet_name
    user.preferred_focus = payload.preferred_focus
    user.note = payload.note
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
