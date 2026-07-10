from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.accounts.models.user import User
from app.modules.accounts.services.auth_service import create_user


def seed_admin_user(db: Session) -> None:
    username = settings.seed_admin_username.strip().lower()
    existing = db.scalar(select(User).where(User.username == username))
    if existing is not None:
        existing.role = "admin"
        existing.is_active = True
        if not existing.display_name:
            existing.display_name = settings.seed_admin_display_name
        db.commit()
        return

    create_user(
        db,
        username=username,
        password=settings.seed_admin_password,
        display_name=settings.seed_admin_display_name,
        role="admin",
    )
