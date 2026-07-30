from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.admin.services.audit_log_service import record_audit_safely
from app.modules.raid_helper.schemas.raid_helper import (
    RaidHelperDestinationRead,
    RaidHelperDestinationWrite,
    RaidHelperProfileCreate,
    RaidHelperProfileRead,
    RaidHelperProfileTestResult,
    RaidHelperProfileWrite,
    RaidHelperTemplateRead,
    RaidHelperTemplateWrite,
)
from app.modules.raid_helper.services.raid_helper_service import (
    RaidHelperError,
    create_profile,
    delete_destination,
    delete_profile,
    delete_template,
    list_destinations,
    list_profiles,
    list_templates,
    save_destination,
    save_template,
    test_profile,
    update_profile,
)

router = APIRouter(prefix="/raid-helper", tags=["admin-raid-helper"])


def _bad(exc: RaidHelperError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/profiles", response_model=list[RaidHelperProfileRead])
def profiles(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return list_profiles(db)


@router.post("/profiles", response_model=RaidHelperProfileRead, status_code=status.HTTP_201_CREATED)
def profile_create(payload: RaidHelperProfileCreate, db: Session = Depends(get_db), actor: User = Depends(require_admin)):
    try:
        row = create_profile(db, payload, actor)
    except RaidHelperError as exc:
        raise _bad(exc) from exc
    record_audit_safely(db, actor=actor, entity_type="raid_helper_profile", entity_id=row.id, action="create", summary=f'Raid-Helper profile “{row.name}” created.', changed_fields=["server_id", "api_key", "api_base_url", "timezone"])
    return row


@router.put("/profiles/{profile_id}", response_model=RaidHelperProfileRead)
def profile_update(profile_id: int, payload: RaidHelperProfileWrite, db: Session = Depends(get_db), actor: User = Depends(require_admin)):
    try:
        row = update_profile(db, profile_id, payload)
    except RaidHelperError as exc:
        raise _bad(exc) from exc
    if row is None:
        raise HTTPException(status_code=404, detail="Raid-Helper profile not found.")
    record_audit_safely(db, actor=actor, entity_type="raid_helper_profile", entity_id=row.id, action="update", summary=f'Raid-Helper profile “{row.name}” updated.', changed_fields=["server_id", "api_key", "api_base_url", "timezone", "is_active"])
    return row


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def profile_delete(profile_id: int, db: Session = Depends(get_db), actor: User = Depends(require_admin)):
    try:
        deleted = delete_profile(db, profile_id)
    except RaidHelperError as exc:
        raise _bad(exc) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Raid-Helper profile not found.")
    record_audit_safely(db, actor=actor, entity_type="raid_helper_profile", entity_id=profile_id, action="delete", summary="Raid-Helper profile deleted.", changed_fields=[])


@router.post("/profiles/{profile_id}/test", response_model=RaidHelperProfileTestResult)
def profile_test(profile_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    result = test_profile(db, profile_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Raid-Helper profile not found.")
    return result


@router.get("/destinations", response_model=list[RaidHelperDestinationRead])
def destinations(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return list_destinations(db)


@router.post("/destinations", response_model=RaidHelperDestinationRead, status_code=status.HTTP_201_CREATED)
def destination_create(payload: RaidHelperDestinationWrite, db: Session = Depends(get_db), actor: User = Depends(require_admin)):
    try:
        row = save_destination(db, payload)
    except RaidHelperError as exc:
        raise _bad(exc) from exc
    record_audit_safely(db, actor=actor, entity_type="raid_helper_destination", entity_id=row.id, action="create", summary=f'Raid-Helper destination “{row.name}” created.', changed_fields=["profile_id", "channel_id", "scope_type", "squad_id", "categories", "is_default", "is_active"])
    return row


@router.put("/destinations/{destination_id}", response_model=RaidHelperDestinationRead)
def destination_update(destination_id: int, payload: RaidHelperDestinationWrite, db: Session = Depends(get_db), actor: User = Depends(require_admin)):
    try:
        row = save_destination(db, payload, destination_id)
    except RaidHelperError as exc:
        if "not found" in str(exc).lower():
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise _bad(exc) from exc
    record_audit_safely(db, actor=actor, entity_type="raid_helper_destination", entity_id=row.id, action="update", summary=f'Raid-Helper destination “{row.name}” updated.', changed_fields=["profile_id", "channel_id", "scope_type", "squad_id", "categories", "is_default", "is_active"])
    return row


@router.delete("/destinations/{destination_id}", status_code=status.HTTP_204_NO_CONTENT)
def destination_delete(destination_id: int, db: Session = Depends(get_db), actor: User = Depends(require_admin)):
    try:
        deleted = delete_destination(db, destination_id)
    except RaidHelperError as exc:
        raise _bad(exc) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Raid-Helper destination not found.")
    record_audit_safely(db, actor=actor, entity_type="raid_helper_destination", entity_id=destination_id, action="delete", summary="Raid-Helper destination deleted.", changed_fields=[])


@router.get("/templates", response_model=list[RaidHelperTemplateRead])
def templates(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return list_templates(db)


@router.post("/templates", response_model=RaidHelperTemplateRead, status_code=status.HTTP_201_CREATED)
def template_create(payload: RaidHelperTemplateWrite, db: Session = Depends(get_db), actor: User = Depends(require_admin)):
    try:
        row = save_template(db, payload)
    except RaidHelperError as exc:
        raise _bad(exc) from exc
    record_audit_safely(db, actor=actor, entity_type="raid_helper_template", entity_id=row.id, action="create", summary=f'Raid-Helper template “{row.name}” created.', changed_fields=["profile_id", "raid_template_id", "scope_type", "categories", "title_template", "description_template", "announcement_template", "payload_template_json", "is_default", "is_active"])
    return row


@router.put("/templates/{template_id}", response_model=RaidHelperTemplateRead)
def template_update(template_id: int, payload: RaidHelperTemplateWrite, db: Session = Depends(get_db), actor: User = Depends(require_admin)):
    try:
        row = save_template(db, payload, template_id)
    except RaidHelperError as exc:
        if "not found" in str(exc).lower():
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise _bad(exc) from exc
    record_audit_safely(db, actor=actor, entity_type="raid_helper_template", entity_id=row.id, action="update", summary=f'Raid-Helper template “{row.name}” updated.', changed_fields=["profile_id", "raid_template_id", "scope_type", "categories", "title_template", "description_template", "announcement_template", "payload_template_json", "is_default", "is_active"])
    return row


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def template_delete(template_id: int, db: Session = Depends(get_db), actor: User = Depends(require_admin)):
    try:
        deleted = delete_template(db, template_id)
    except RaidHelperError as exc:
        raise _bad(exc) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Raid-Helper template not found.")
    record_audit_safely(db, actor=actor, entity_type="raid_helper_template", entity_id=template_id, action="delete", summary="Raid-Helper template deleted.", changed_fields=[])
