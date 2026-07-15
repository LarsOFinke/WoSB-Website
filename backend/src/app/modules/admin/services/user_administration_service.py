from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.accounts.models.user import ROLE_ADMIN, User
from app.modules.accounts.services.auth_service import revoke_user_sessions
from app.modules.admin.schemas.user_administration import UserAdministrationUpdate
from app.modules.permissions.models.role import SiteRoleDefinition
from app.modules.permissions.services.role_service import assign_site_role


class UserAdministrationError(ValueError):
    pass


def _active_admin_count(db: Session) -> int:
    return int(
        db.scalar(
            select(func.count(User.id))
            .join(User.site_role)
            .where(SiteRoleDefinition.code == ROLE_ADMIN, User.is_active.is_(True))
        )
        or 0
    )


def update_user_account(
    db: Session,
    *,
    actor: User,
    target_id: int,
    payload: UserAdministrationUpdate,
) -> User:
    target = db.get(User, target_id)
    if target is None:
        raise UserAdministrationError("User not found.")

    if target.id == actor.id:
        if payload.is_active is False:
            raise UserAdministrationError("You cannot deactivate your own account.")
        if payload.role is not None and payload.role != actor.role:
            raise UserAdministrationError("You cannot change your own site role.")

    # Strict hierarchy: nobody may alter an account at their own or a higher
    # authority level. This permanently prevents moderators from disabling or
    # demoting administrators and prevents peer-admin account takeovers.
    if target.id != actor.id and target.role_rank >= actor.role_rank:
        raise UserAdministrationError("You cannot modify an account with an equal or higher role.")

    security_state_changed = False

    if payload.role is not None:
        if not actor.is_admin:
            raise UserAdministrationError("Only administrators can change site roles.")
        if target.role == ROLE_ADMIN and payload.role != ROLE_ADMIN:
            raise UserAdministrationError("Administrator accounts cannot be demoted by another account.")
        if payload.role != target.role:
            assign_site_role(db, target, payload.role)
            security_state_changed = True

    if payload.is_active is not None:
        if target.role == ROLE_ADMIN and payload.is_active is False:
            raise UserAdministrationError("Administrator accounts cannot be deactivated by another account.")
        if target.role == ROLE_ADMIN and _active_admin_count(db) <= 1 and payload.is_active is False:
            raise UserAdministrationError("The last active administrator cannot be deactivated.")
        if payload.is_active != target.is_active:
            target.is_active = payload.is_active
            security_state_changed = True

    if security_state_changed:
        revoke_user_sessions(db, target.id, commit=False)

    db.commit()
    db.refresh(target)
    return target
