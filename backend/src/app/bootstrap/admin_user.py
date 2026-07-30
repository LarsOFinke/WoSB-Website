from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.accounts.models.user import User
from app.modules.accounts.services.auth_service import create_user
from app.modules.permissions.services.role_service import assign_site_role


def seed_admin_user(db: Session) -> None:
    username = settings.seed_admin_username.strip().lower()
    if not username:
        existing_admin = db.scalar(
            select(User)
            .join(User.site_role)
            .where(User.site_role.has(code="admin"), User.is_active.is_(True))
            .order_by(User.is_bootstrap_admin.desc(), User.id)
        )
        if existing_admin is not None:
            db.execute(
                update(User)
                .where(User.id != existing_admin.id, User.is_bootstrap_admin.is_(True))
                .values(is_bootstrap_admin=False)
            )
            existing_admin.is_bootstrap_admin = True
            db.commit()
            return
        raise RuntimeError("SEED_ADMIN_USERNAME is required when no administrator account exists.")
    existing = db.scalar(select(User).where(User.username == username))
    if existing is not None:
        db.execute(
            update(User)
            .where(User.id != existing.id, User.is_bootstrap_admin.is_(True))
            .values(is_bootstrap_admin=False)
        )
        assign_site_role(db, existing, "admin")
        existing.is_active = True
        existing.is_bootstrap_admin = True
        if not existing.display_name:
            existing.display_name = settings.seed_admin_display_name
        db.commit()
        return

    db.execute(update(User).where(User.is_bootstrap_admin.is_(True)).values(is_bootstrap_admin=False))
    created = create_user(
        db,
        username=username,
        password=settings.seed_admin_password,
        display_name=settings.seed_admin_display_name,
        role="admin",
    )
    created.is_bootstrap_admin = True
    db.commit()
