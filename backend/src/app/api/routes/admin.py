from fastapi import APIRouter

from app.api.dependencies import AdminUser, DbSession
from app.schemas.group import GroupRead
from app.services import GroupService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/groups", response_model=list[GroupRead])
def list_all_groups_for_admin(db: DbSession, user: AdminUser) -> list[GroupRead]:
    return GroupService(db).list_groups(viewer=user, include_inactive=True)
