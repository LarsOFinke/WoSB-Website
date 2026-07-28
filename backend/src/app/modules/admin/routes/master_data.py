from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.db.session import get_db
from app.modules.accounts.models.user import User
from app.modules.admin.schemas.master_data import (
    MasterDataCategoryCreate,
    MasterDataCategoryRead,
    MasterDataCategoryUpdate,
    MasterDataOptionCreate,
    MasterDataOptionRead,
    MasterDataOptionUpdate,
    MasterDataOverview,
    MasterDataSeedRestoreSummary,
    MasterDataShipCreate,
    MasterDataShipRead,
    MasterDataShipUpdate,
    MasterDataTaxonomyRead,
)
from app.modules.admin.services.audit_log_service import record_audit_safely
from app.modules.admin.services.master_data_service import (
    MasterDataError,
    create_category,
    create_option,
    create_ship,
    deactivate_category,
    deactivate_option,
    deactivate_ship,
    get_taxonomy,
    list_categories,
    list_options,
    list_ships,
    master_data_overview,
    restore_all_seed_defaults,
    restore_category_seed,
    restore_option_seed,
    restore_ship_seed,
    update_category,
    update_option,
    update_ship,
)


router = APIRouter(prefix="/master-data", tags=["admin-master-data"])


def _bad_request(exc: MasterDataError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/overview", response_model=MasterDataOverview)
def overview(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> MasterDataOverview:
    return master_data_overview(db)


@router.post("/restore-seed-defaults", response_model=MasterDataSeedRestoreSummary)
def restore_seed_defaults(
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin),
) -> MasterDataSeedRestoreSummary:
    try:
        result = restore_all_seed_defaults(db)
    except (MasterDataError, ValueError) as exc:
        raise _bad_request(MasterDataError(str(exc))) from exc
    record_audit_safely(
        db,
        actor=actor,
        entity_type="master_data",
        entity_id="repository-seed-defaults",
        action="restore_seed_defaults",
        summary=(
            "Repository-owned master data restored "
            f"(categories={result.categories}, options={result.options}, ships={result.ships}, "
            f"overrides_discarded={result.overrides_discarded})."
        ),
        changed_fields=["categories", "options", "ships"],
    )
    return result


@router.get("/taxonomy", response_model=MasterDataTaxonomyRead)
def taxonomy(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> MasterDataTaxonomyRead:
    return get_taxonomy(db)


@router.get("/categories", response_model=list[MasterDataCategoryRead])
def categories(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[MasterDataCategoryRead]:
    return list_categories(db)


@router.post("/categories", response_model=MasterDataCategoryRead, status_code=status.HTTP_201_CREATED)
def post_category(
    payload: MasterDataCategoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> MasterDataCategoryRead:
    try:
        return create_category(db, payload)
    except MasterDataError as exc:
        raise _bad_request(exc) from exc


@router.put("/categories/{category_id}", response_model=MasterDataCategoryRead)
def put_category(
    category_id: int,
    payload: MasterDataCategoryUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> MasterDataCategoryRead:
    try:
        return update_category(db, category_id, payload)
    except MasterDataError as exc:
        raise _bad_request(exc) from exc


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    try:
        deactivate_category(db, category_id)
    except MasterDataError as exc:
        raise _bad_request(exc) from exc


@router.post("/categories/{category_id}/restore-seed", response_model=MasterDataCategoryRead)
def restore_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> MasterDataCategoryRead:
    try:
        return restore_category_seed(db, category_id)
    except MasterDataError as exc:
        raise _bad_request(exc) from exc


@router.get("/options", response_model=list[MasterDataOptionRead])
def options(
    category: str | None = Query(default=None, max_length=40),
    search: str | None = Query(default=None, max_length=160),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[MasterDataOptionRead]:
    return list_options(db, category_key=category, search=search)


@router.post("/options", response_model=MasterDataOptionRead, status_code=status.HTTP_201_CREATED)
def post_option(
    payload: MasterDataOptionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> MasterDataOptionRead:
    try:
        return create_option(db, payload)
    except MasterDataError as exc:
        raise _bad_request(exc) from exc


@router.put("/options/{option_id}", response_model=MasterDataOptionRead)
def put_option(
    option_id: int,
    payload: MasterDataOptionUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> MasterDataOptionRead:
    try:
        return update_option(db, option_id, payload)
    except MasterDataError as exc:
        raise _bad_request(exc) from exc


@router.delete("/options/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_option(
    option_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    try:
        deactivate_option(db, option_id)
    except MasterDataError as exc:
        raise _bad_request(exc) from exc


@router.post("/options/{option_id}/restore-seed", response_model=MasterDataOptionRead)
def restore_option(
    option_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> MasterDataOptionRead:
    try:
        return restore_option_seed(db, option_id)
    except MasterDataError as exc:
        raise _bad_request(exc) from exc


@router.get("/ships", response_model=list[MasterDataShipRead])
def ships(
    search: str | None = Query(default=None, max_length=120),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[MasterDataShipRead]:
    return list_ships(db, search=search)


@router.post("/ships", response_model=MasterDataShipRead, status_code=status.HTTP_201_CREATED)
def post_ship(
    payload: MasterDataShipCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> MasterDataShipRead:
    try:
        return create_ship(db, payload)
    except MasterDataError as exc:
        raise _bad_request(exc) from exc


@router.put("/ships/{ship_id}", response_model=MasterDataShipRead)
def put_ship(
    ship_id: int,
    payload: MasterDataShipUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> MasterDataShipRead:
    try:
        return update_ship(db, ship_id, payload)
    except MasterDataError as exc:
        raise _bad_request(exc) from exc


@router.delete("/ships/{ship_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ship(
    ship_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    try:
        deactivate_ship(db, ship_id)
    except MasterDataError as exc:
        raise _bad_request(exc) from exc


@router.post("/ships/{ship_id}/restore-seed", response_model=MasterDataShipRead)
def restore_ship(
    ship_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> MasterDataShipRead:
    try:
        return restore_ship_seed(db, ship_id)
    except MasterDataError as exc:
        raise _bad_request(exc) from exc
