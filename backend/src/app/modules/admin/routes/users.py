from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin, require_staff
from app.db.session import get_db
from app.modules.accounts.models.user import ROLE_MODERATOR, User
from app.modules.accounts.schemas.user_read import UserRead
from app.modules.accounts.services.auth_service import AuthError, create_user
from app.modules.admin.schemas.moderator_create import ModeratorCreate
from app.modules.admin.schemas.moderator_create_response import ModeratorCreateResponse
from app.modules.admin.schemas.user_administration import UserAdministrationUpdate
from app.modules.admin.services.audit_log_service import record_audit_safely
from app.modules.admin.services.user_administration_service import (
    UserAdministrationError,
    update_user_account,
)

router = APIRouter(tags=["admin-users"])


@router.get("/users", response_model=list[UserRead])
def admin_list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[UserRead]:
    users = db.scalars(select(User).order_by(User.created_at.desc(), User.id.desc())).all()
    return [UserRead.model_validate(user) for user in users]


@router.put("/users/{user_id}", response_model=UserRead)
def admin_update_user(
    user_id: int,
    payload: UserAdministrationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> UserRead:
    existing = db.get(User, user_id)
    previous_role = existing.role if existing is not None else None
    previous_active = existing.is_active if existing is not None else None
    try:
        user = update_user_account(db, actor=current_user, target_id=user_id, payload=payload)
    except UserAdministrationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    changed_fields = []
    if previous_role != user.role:
        changed_fields.append("role")
    if previous_active != user.is_active:
        changed_fields.append("is_active")
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="user_account",
        entity_id=user.id,
        action="update",
        summary=f'Account “{user.username}” updated.',
        changed_fields=changed_fields,
    )
    return UserRead.model_validate(user)


@router.post(
    "/moderators",
    response_model=ModeratorCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_moderator(
    payload: ModeratorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> ModeratorCreateResponse:
    try:
        user = create_user(
            db,
            username=payload.username,
            password=payload.password,
            display_name=payload.display_name,
            role=ROLE_MODERATOR,
        )
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    record_audit_safely(
        db,
        actor=current_user,
        entity_type="user_account",
        entity_id=user.id,
        action="create",
        summary=f'Moderator account “{user.username}” created.',
        changed_fields=["username", "display_name", "role", "is_active"],
    )
    return ModeratorCreateResponse(user=UserRead.model_validate(user))
