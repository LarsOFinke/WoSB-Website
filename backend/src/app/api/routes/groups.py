from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, DbSession, OptionalCurrentUser
from app.schemas.group import GroupCreate, GroupParticipantCreate, GroupRead, GroupUpdate
from app.services import GroupFullError, GroupNotFoundError, GroupPermissionError, GroupService

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("", response_model=list[GroupRead])
def list_groups(db: DbSession, user: OptionalCurrentUser) -> list[GroupRead]:
    return GroupService(db).list_groups(viewer=user)


@router.get("/manageable", response_model=list[GroupRead])
def list_manageable_groups(db: DbSession, user: CurrentUser) -> list[GroupRead]:
    return GroupService(db).list_manageable_groups(viewer=user)


@router.get("/{group_id}", response_model=GroupRead)
def get_group(group_id: int, db: DbSession, user: OptionalCurrentUser) -> GroupRead:
    group = GroupService(db).get_group(group_id, viewer=user)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gruppe nicht gefunden.")
    return group


@router.post("", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
def create_group(payload: GroupCreate, db: DbSession, user: CurrentUser) -> GroupRead:
    try:
        return GroupService(db).create_group(payload, owner=user)
    except GroupPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/{group_id}", response_model=GroupRead)
def update_group(group_id: int, payload: GroupUpdate, db: DbSession, user: CurrentUser) -> GroupRead:
    try:
        return GroupService(db).update_group(group_id, payload, actor=user)
    except GroupNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except GroupPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/{group_id}/close", response_model=GroupRead)
def close_group(group_id: int, db: DbSession, user: CurrentUser) -> GroupRead:
    try:
        return GroupService(db).close_group(group_id, actor=user)
    except GroupNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except GroupPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_id: int, db: DbSession, user: CurrentUser) -> None:
    try:
        GroupService(db).delete_group(group_id, actor=user)
    except GroupNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except GroupPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/{group_id}/join", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
def join_group(group_id: int, payload: GroupParticipantCreate, db: DbSession, user: OptionalCurrentUser) -> GroupRead:
    try:
        return GroupService(db).join_group(group_id, payload, actor=user)
    except GroupNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except GroupFullError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except GroupPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/participations/{join_token}", status_code=status.HTTP_204_NO_CONTENT)
def leave_group(join_token: str, db: DbSession) -> None:
    try:
        GroupService(db).leave_group_by_token(join_token)
    except GroupNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
