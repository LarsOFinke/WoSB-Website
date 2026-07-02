from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Profile


class ProfileRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user_id(self, user_id: int) -> Profile | None:
        stmt = select(Profile).where(Profile.user_id == user_id).options(selectinload(Profile.user), selectinload(Profile.preferred_ship))
        return self.db.scalars(stmt).first()
