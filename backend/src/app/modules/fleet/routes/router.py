from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin, require_user
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.admin.services.audit_log_service import record_audit_safely
from app.modules.fleet.models.fleet_membership import FleetMembership
from app.modules.fleet.schemas.fleet_create import FleetCreate
from app.modules.fleet.schemas.fleet_detail import FleetDetail
from app.modules.fleet.schemas.fleet_join_request import FleetJoinRequest
from app.modules.fleet.schemas.fleet_membership_management import FleetMembershipManagementRead
from app.modules.fleet.schemas.fleet_membership_read import FleetMembershipRead
from app.modules.fleet.schemas.fleet_membership_self_read import FleetMembershipSelfRead
from app.modules.fleet.schemas.fleet_membership_update import FleetMembershipUpdate
from app.modules.fleet.schemas.fleet_public import FleetPublicLeaderRead, FleetPublicRead
from app.modules.fleet.schemas.fleet_read import FleetRead
from app.modules.fleet.schemas.fleet_update import FleetUpdate
from app.modules.fleet.services.fleet_management_policy import (
    FleetManagementContext,
    FleetMembershipPermissionError,
    build_management_context,
    membership_permissions,
)
from app.modules.fleet.services.fleet_service import (
    FleetValidationError,
    assign_fleet_role,
    can_manage_fleet,
    create_fleet,
    get_fleet,
    join_fleet,
    list_fleets,
    list_user_memberships,
    update_fleet,
    update_membership,
    user_leadership_memberships,
)

router = APIRouter(prefix="/fleets", tags=["fleets"])


def _membership_read(
    membership: FleetMembership,
    context: FleetManagementContext | None = None,
) -> FleetMembershipRead:
    result = FleetMembershipRead.model_validate(membership)
    if context is not None:
        permissions = membership_permissions(context, membership)
        result.management = FleetMembershipManagementRead(
            can_edit_directory=permissions.can_edit_directory,
            can_change_role=permissions.can_change_role,
            can_change_status=permissions.can_change_status,
            assignable_roles=list(permissions.assignable_roles),
            protected=permissions.protected,
            reason=permissions.reason,
        )
    return result


def _fleet_detail_for_actor(
    db: Session,
    fleet,
    actor: User,
) -> FleetDetail:
    result = FleetDetail.model_validate(fleet)
    context = build_management_context(db, actor, fleet.id)
    result.memberships = [_membership_read(row, context) for row in fleet.memberships]
    return result


@router.get("/public/official", response_model=FleetPublicRead)
def get_public_official_fleet(db: Session = Depends(get_db)) -> FleetPublicRead:
    fleets = list_fleets(db)
    if not fleets:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fleet not found.")
    fleet = fleets[0]
    return FleetPublicRead(
        id=fleet.id,
        name=fleet.name,
        slug=fleet.slug,
        focus=fleet.focus,
        description=fleet.description,
        standing_orders=fleet.standing_orders,
        active_members_count=fleet.active_members_count,
        leaders=[
            FleetPublicLeaderRead(
                display_name=row.user.display_name,
                role=row.role,
                role_label=row.fleet_role.label if row.fleet_role else row.role,
            )
            for row in fleet.leaders
        ],
    )


@router.get("", response_model=list[FleetRead])
def get_fleets(
    db: Session = Depends(get_db),
    _: User = Depends(require_user),
) -> list[FleetRead]:
    return list_fleets(db)


@router.get("/manageable", response_model=list[FleetRead])
def get_manageable_fleets(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> list[FleetRead]:
    if current_user.can_moderate:
        return list_fleets(db, include_inactive=True)
    memberships = user_leadership_memberships(db, current_user)
    if not memberships:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Fleet leadership access required.")
    fleets = [get_fleet(db, membership.fleet_id) for membership in memberships]
    return [fleet for fleet in fleets if fleet is not None]


@router.get("/memberships/me", response_model=list[FleetMembershipSelfRead])
def get_my_fleet_memberships(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> list[FleetMembershipSelfRead]:
    return [FleetMembershipSelfRead.model_validate(row) for row in list_user_memberships(db, current_user)]


@router.post("", response_model=FleetRead, status_code=status.HTTP_201_CREATED)
def post_fleet(
    payload: FleetCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> FleetRead:
    try:
        return create_fleet(db, payload)
    except FleetValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/join", response_model=FleetMembershipRead, status_code=status.HTTP_201_CREATED)
def post_fleet_join(
    payload: FleetJoinRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> FleetMembershipRead:
    try:
        membership = join_fleet(db, current_user, payload)
        return FleetMembershipRead.model_validate(membership)
    except FleetValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{fleet_id}", response_model=FleetDetail)
def get_fleet_detail(
    fleet_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_user),
) -> FleetDetail:
    fleet = get_fleet(db, fleet_id, include_members=False)
    if fleet is None or not fleet.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fleet not found.")
    return FleetDetail.model_validate(fleet)


@router.get("/{fleet_id}/manage", response_model=FleetDetail)
def get_fleet_management_detail(
    fleet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> FleetDetail:
    if not can_manage_fleet(db, current_user, fleet_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Fleet leadership access required.")
    fleet = get_fleet(db, fleet_id, include_members=True)
    if fleet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fleet not found.")
    return _fleet_detail_for_actor(db, fleet, current_user)


@router.put("/{fleet_id}", response_model=FleetRead)
def put_fleet(
    fleet_id: int,
    payload: FleetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> FleetRead:
    if not can_manage_fleet(db, current_user, fleet_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Fleet leadership access required.")
    try:
        fleet = update_fleet(db, fleet_id, payload)
    except FleetValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if fleet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fleet not found.")
    return fleet


@router.put("/{fleet_id}/memberships/{membership_id}", response_model=FleetMembershipRead)
def put_membership(
    fleet_id: int,
    membership_id: int,
    payload: FleetMembershipUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> FleetMembershipRead:
    if not can_manage_fleet(db, current_user, fleet_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Fleet leadership access required.")
    membership = db.get(FleetMembership, membership_id)
    if membership is None or membership.fleet_id != fleet_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found.")
    try:
        updated = update_membership(db, membership_id, payload, actor=current_user)
    except FleetMembershipPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except FleetValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found.")
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="fleet_membership",
        entity_id=updated.id,
        action="update",
        summary=f"Updated fleet membership for {updated.user.display_name}.",
        changed_fields=payload.model_fields_set,
    )
    context = build_management_context(db, current_user, fleet_id)
    return _membership_read(updated, context)


@router.post("/{fleet_id}/leaders/{user_id}", response_model=FleetMembershipRead)
def post_fleet_leader(
    fleet_id: int,
    user_id: int,
    payload: FleetMembershipUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> FleetMembershipRead:
    role = payload.role or "fleet_admiral"
    try:
        return FleetMembershipRead.model_validate(assign_fleet_role(db, fleet_id, user_id, role))
    except FleetValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
