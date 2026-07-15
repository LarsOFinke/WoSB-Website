from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.accounts.models.user import ROLE_ADMIN, ROLE_MODERATOR, User
from app.modules.fleet.models.fleet import FLEET_MEMBER_ACTIVE, FLEET_ROLE_ADMIRAL
from app.modules.fleet.models.fleet_membership import FleetMembership
from app.modules.permissions.models.role import FleetRoleDefinition


@dataclass(frozen=True, slots=True)
class FleetRolePolicyItem:
    code: str
    rank: int
    can_manage_members: bool


@dataclass(frozen=True, slots=True)
class FleetManagementContext:
    actor: User
    fleet_id: int
    actor_fleet_role: str | None
    actor_fleet_rank: int
    actor_can_manage_members: bool
    active_admiral_count: int
    active_roles: tuple[FleetRolePolicyItem, ...]

    @property
    def actor_kind(self) -> str:
        if self.actor.role == ROLE_ADMIN:
            return ROLE_ADMIN
        if self.actor.role == ROLE_MODERATOR:
            return ROLE_MODERATOR
        return self.actor_fleet_role or "member"


@dataclass(frozen=True, slots=True)
class FleetMembershipPermissions:
    can_edit_directory: bool
    can_change_role: bool
    can_change_status: bool
    assignable_roles: tuple[str, ...]
    protected: bool
    reason: str | None


class FleetMembershipPermissionError(ValueError):
    pass


def build_management_context(db: Session, actor: User, fleet_id: int) -> FleetManagementContext:
    actor_membership = db.scalar(
        select(FleetMembership)
        .where(
            FleetMembership.fleet_id == fleet_id,
            FleetMembership.user_id == actor.id,
            FleetMembership.status == FLEET_MEMBER_ACTIVE,
        )
    )
    active_admiral_count = int(
        db.scalar(
            select(func.count(FleetMembership.id))
            .join(FleetMembership.fleet_role)
            .where(
                FleetMembership.fleet_id == fleet_id,
                FleetMembership.status == FLEET_MEMBER_ACTIVE,
                FleetRoleDefinition.code == FLEET_ROLE_ADMIRAL,
            )
        )
        or 0
    )
    roles = tuple(
        FleetRolePolicyItem(
            code=row.code,
            rank=int(row.rank),
            can_manage_members=bool(row.can_manage_members),
        )
        for row in db.scalars(
            select(FleetRoleDefinition)
            .where(FleetRoleDefinition.is_active.is_(True))
            .order_by(FleetRoleDefinition.rank.asc(), FleetRoleDefinition.code.asc())
        ).all()
    )
    actor_role = actor_membership.fleet_role if actor_membership else None
    return FleetManagementContext(
        actor=actor,
        fleet_id=fleet_id,
        actor_fleet_role=actor_role.code if actor_role else None,
        actor_fleet_rank=int(actor_role.rank) if actor_role else 0,
        actor_can_manage_members=bool(actor_role.can_manage_members) if actor_role else False,
        active_admiral_count=active_admiral_count,
        active_roles=roles,
    )


def _base_permissions(
    *,
    assignable_roles: tuple[str, ...] = (),
    can_edit_directory: bool = False,
    can_change_role: bool = False,
    can_change_status: bool = False,
    reason: str | None = None,
) -> FleetMembershipPermissions:
    return FleetMembershipPermissions(
        can_edit_directory=can_edit_directory,
        can_change_role=can_change_role,
        can_change_status=can_change_status,
        assignable_roles=assignable_roles,
        protected=reason is not None or not (can_edit_directory or can_change_role or can_change_status),
        reason=reason,
    )


def _roles_below(context: FleetManagementContext, rank: int) -> tuple[str, ...]:
    return tuple(role.code for role in context.active_roles if role.rank < rank)


def membership_permissions(
    context: FleetManagementContext,
    target: FleetMembership,
) -> FleetMembershipPermissions:
    actor = context.actor
    target_user = target.user
    last_active_admiral = (
        target.role == FLEET_ROLE_ADMIRAL
        and target.status == FLEET_MEMBER_ACTIVE
        and context.active_admiral_count <= 1
    )

    if actor.is_admin:
        return _base_permissions(
            assignable_roles=tuple(role.code for role in context.active_roles),
            can_edit_directory=True,
            can_change_role=not last_active_admiral,
            can_change_status=not last_active_admiral,
            reason="last_admiral" if last_active_admiral else None,
        )

    if target.user_id == actor.id:
        return _base_permissions(reason="self")
    if target_user.role == ROLE_ADMIN:
        return _base_permissions(reason="site_admin")
    if target_user.role == ROLE_MODERATOR:
        return _base_permissions(reason="site_peer")
    if target.role == FLEET_ROLE_ADMIRAL:
        return _base_permissions(reason="fleet_admiral")

    admiral_rank = max(
        (role.rank for role in context.active_roles if role.code == FLEET_ROLE_ADMIRAL),
        default=80,
    )
    if actor.role == ROLE_MODERATOR:
        return _base_permissions(
            assignable_roles=_roles_below(context, admiral_rank),
            can_edit_directory=True,
            can_change_role=True,
            can_change_status=True,
        )

    if context.actor_can_manage_members:
        if target.role_rank >= context.actor_fleet_rank:
            return _base_permissions(reason="fleet_peer")
        return _base_permissions(
            assignable_roles=_roles_below(context, context.actor_fleet_rank),
            can_edit_directory=True,
            can_change_role=True,
            can_change_status=True,
        )

    return _base_permissions(reason="insufficient")


def validate_membership_update(
    db: Session,
    *,
    actor: User,
    target: FleetMembership,
    changed_fields: set[str],
    requested_role: str | None,
) -> FleetMembershipPermissions:
    context = build_management_context(db, actor, target.fleet_id)
    permissions = membership_permissions(context, target)

    directory_fields = {"note", "assignment", "admin_note"}
    if changed_fields & directory_fields and not permissions.can_edit_directory:
        raise FleetMembershipPermissionError("You cannot edit this protected fleet membership.")
    if "status" in changed_fields and not permissions.can_change_status:
        if permissions.reason == "last_admiral":
            raise FleetMembershipPermissionError("The last active fleet admiral cannot be deactivated.")
        raise FleetMembershipPermissionError("You cannot change the status of this protected fleet membership.")
    if "role" in changed_fields:
        if not permissions.can_change_role:
            if permissions.reason == "last_admiral":
                raise FleetMembershipPermissionError("The last active fleet admiral cannot be demoted.")
            raise FleetMembershipPermissionError("You cannot change the role of this protected fleet membership.")
        if requested_role not in permissions.assignable_roles:
            raise FleetMembershipPermissionError("You cannot assign this fleet role.")

    return permissions
