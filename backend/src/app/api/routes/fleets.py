from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin, require_user
from app.db.session import get_db
from app.models import FleetMembership, User
from app.schemas import FleetCreate, FleetDetail, FleetJoinRequest, FleetMembershipRead, FleetMembershipSelfRead, FleetMembershipUpdate, FleetRead, FleetUpdate
from app.services.fleet_service import (
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


@router.get("", response_model=list[FleetRead])
def get_fleets(db: Session = Depends(get_db)) -> list[FleetRead]:
    return list_fleets(db)


@router.get("/manageable", response_model=list[FleetRead])
def get_manageable_fleets(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> list[FleetRead]:
    if current_user.is_admin:
        return list_fleets(db, include_inactive=True)
    memberships = user_leadership_memberships(db, current_user)
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
def get_fleet_detail(fleet_id: int, db: Session = Depends(get_db)) -> FleetDetail:
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
    return FleetDetail.model_validate(fleet)


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
        updated = update_membership(db, membership_id, payload)
    except FleetValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found.")
    return FleetMembershipRead.model_validate(updated)


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
