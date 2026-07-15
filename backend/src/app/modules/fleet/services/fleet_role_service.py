from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.accounts.models.user import User
from app.modules.fleet.models.fleet import FLEET_MEMBER_ACTIVE, FLEET_ROLE_ADMIRAL
from app.modules.fleet.models.fleet_membership import FleetMembership
from app.modules.fleet.schemas.fleet_role import FleetRoleCreate, FleetRoleRead, FleetRoleUpdate
from app.modules.permissions.models.role import FleetRoleDefinition


class FleetRoleValidationError(ValueError):
    pass


class FleetRolePermissionError(PermissionError):
    pass


def can_manage_fleet_roles(db: Session, actor: User, fleet_id: int) -> bool:
    if actor.is_admin:
        return True
    membership = db.scalar(
        select(FleetMembership)
        .join(FleetMembership.fleet_role)
        .where(
            FleetMembership.fleet_id == fleet_id,
            FleetMembership.user_id == actor.id,
            FleetMembership.status == FLEET_MEMBER_ACTIVE,
            FleetRoleDefinition.code == FLEET_ROLE_ADMIRAL,
        )
    )
    return membership is not None


def _require_permission(db: Session, actor: User, fleet_id: int) -> None:
    if not can_manage_fleet_roles(db, actor, fleet_id):
        raise FleetRolePermissionError("Fleet admiral access required to manage fleet roles.")


def _member_counts(db: Session) -> dict[int, int]:
    return {
        int(role_id): int(count)
        for role_id, count in db.execute(
            select(FleetMembership.fleet_role_id, func.count(FleetMembership.id)).group_by(
                FleetMembership.fleet_role_id
            )
        ).all()
    }


def _serialize(row: FleetRoleDefinition, counts: dict[int, int]) -> FleetRoleRead:
    return FleetRoleRead(
        id=row.id,
        code=row.code,
        label=row.label,
        rank=row.rank,
        is_leadership=row.is_leadership,
        can_manage_fleet=row.can_manage_fleet,
        can_manage_members=row.can_manage_members,
        is_system=row.is_system,
        is_active=row.is_active,
        member_count=counts.get(row.id, 0),
    )


def list_fleet_roles(
    db: Session,
    *,
    include_inactive: bool = False,
) -> list[FleetRoleRead]:
    query = select(FleetRoleDefinition)
    if not include_inactive:
        query = query.where(FleetRoleDefinition.is_active.is_(True))
    rows = db.scalars(
        query.order_by(FleetRoleDefinition.rank.desc(), FleetRoleDefinition.label.asc())
    ).all()
    counts = _member_counts(db)
    return [_serialize(row, counts) for row in rows]


def create_fleet_role(
    db: Session,
    fleet_id: int,
    payload: FleetRoleCreate,
    actor: User,
) -> FleetRoleRead:
    _require_permission(db, actor, fleet_id)
    if db.scalar(select(FleetRoleDefinition.id).where(FleetRoleDefinition.code == payload.code)):
        raise FleetRoleValidationError("A fleet role with this code already exists.")
    row = FleetRoleDefinition(
        code=payload.code,
        label=payload.label,
        rank=payload.rank,
        is_leadership=payload.is_leadership,
        can_manage_fleet=payload.can_manage_fleet,
        can_manage_members=payload.can_manage_members,
        is_system=False,
        is_active=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize(row, {})


def update_fleet_role(
    db: Session,
    fleet_id: int,
    role_id: int,
    payload: FleetRoleUpdate,
    actor: User,
) -> FleetRoleRead | None:
    _require_permission(db, actor, fleet_id)
    row = db.get(FleetRoleDefinition, role_id)
    if row is None:
        return None
    if row.is_system:
        raise FleetRoleValidationError("System fleet roles cannot be changed.")
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(row, field, value)
    if row.can_manage_fleet or row.can_manage_members:
        row.is_leadership = True
    if data.get("is_active") is False:
        used = db.scalar(
            select(func.count(FleetMembership.id)).where(FleetMembership.fleet_role_id == row.id)
        )
        if used:
            raise FleetRoleValidationError(
                "Reassign all members before deactivating this fleet role."
            )
    db.commit()
    db.refresh(row)
    return _serialize(row, _member_counts(db))


def delete_fleet_role(
    db: Session,
    fleet_id: int,
    role_id: int,
    actor: User,
) -> bool:
    _require_permission(db, actor, fleet_id)
    row = db.get(FleetRoleDefinition, role_id)
    if row is None:
        return False
    if row.is_system:
        raise FleetRoleValidationError("System fleet roles cannot be deleted.")
    used = db.scalar(
        select(func.count(FleetMembership.id)).where(FleetMembership.fleet_role_id == row.id)
    )
    if used:
        raise FleetRoleValidationError("Reassign all members before deleting this fleet role.")
    db.delete(row)
    db.commit()
    return True
