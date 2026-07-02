from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username.lower())
        return self.db.scalars(stmt).first()

    def create(self, user: User) -> User:
        user.username = user.username.lower()
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user
