from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.builds.models.build import Build
from app.modules.builds.models.build_classification import BuildClassification
from app.modules.builds.models.build_feature import BuildFeatureDefinition
from app.modules.builds.models.build_slot import BuildSlot
from app.modules.builds.models.build_role import BuildRole
from app.modules.builds.models.build_vote import BuildVote
from app.modules.builds.schemas.build_create import BuildCreate
from app.modules.builds.schemas.constants import BUILD_CLASSIFICATION_VALUES
from app.modules.builds.schemas.build_summary import (
    BuildListMetrics,
    BuildPage,
    BuildSummaryRead,
)
from app.modules.builds.services.build_validation import (
    BuildValidationError,
    validate_and_prepare_build,
)
from app.modules.ships.models.ship import Ship
from app.modules.ships.schemas.ship import ShipRead
from app.modules.builds.services.ship_upgrade_effect_service import effective_upgrade_effects
from app.modules.builds.services.upgrade_slot_service import calculate_upgrade_slot_access
from app.modules.builds.services.build_printout_service import public_printout_url
from app.modules.builds.services.build_deletion_service import delete_build_and_files

__all__ = [
    "BuildValidationError",
    "create_build",
    "delete_build",
    "delete_user_build",
    "get_build",
    "list_build_page",
    "list_builds",
    "list_user_build_page",
    "list_user_builds",
    "update_user_build",
]


def _build_query():
    return select(Build).options(
        selectinload(Build.slots).selectinload(BuildSlot.option),
        selectinload(Build.classifications),
        selectinload(Build.research_upgrade_feature).selectinload(BuildFeatureDefinition.effects),
    )


def _decorate_builds(
    db: Session,
    builds: list[Build],
    viewer_id: int | None = None,
) -> list[Build]:
    if not builds:
        return builds
    role_labels = {row.slug: row.label for row in db.scalars(select(BuildRole)).all()}
    vote_counts = dict(
        db.execute(
            select(BuildVote.build_id, func.count(BuildVote.id))
            .where(BuildVote.build_id.in_([build.id for build in builds]))
            .group_by(BuildVote.build_id)
        ).all()
    )
    voted_build_ids: set[int] = set()
    if viewer_id is not None:
        voted_build_ids = set(
            db.scalars(
                select(BuildVote.build_id).where(
                    BuildVote.user_id == viewer_id,
                    BuildVote.build_id.in_([build.id for build in builds]),
                )
            ).all()
        )
    for build in builds:
        build._build_role_label = role_labels.get(
            build.build_type,
            build.build_type.replace("_", " ").title(),
        )
        build._upvote_count = int(vote_counts.get(build.id, 0))
        build._viewer_has_upvoted = build.id in voted_build_ids
    return builds


def _apply_build_filters(
    statement,
    *,
    search: str | None = None,
    build_type: str | None = None,
    classification: str | None = None,
    owner_id: int | None = None,
):
    if search:
        like = f"%{search.strip()}%"
        statement = statement.where(
            Build.build_name.ilike(like) | Ship.name.ilike(like) | Build.build_type.ilike(like)
        )
    if build_type:
        statement = statement.where(Build.build_type == build_type.strip().lower())
    if classification:
        normalized_classification = classification.strip().lower()
        if normalized_classification in BUILD_CLASSIFICATION_VALUES:
            statement = statement.where(
                Build.classifications.any(BuildClassification.tag == normalized_classification)
            )
    if owner_id is not None:
        statement = statement.where(Build.owner_id == owner_id)
    return statement


def _summary_for_build(build: Build) -> BuildSummaryRead:
    upgrade_slots = [slot for slot in build.slots if slot.slot_type == "upgrade"]
    unlock_effect_slots = sum(
        max(
            0,
            int(
                effective_upgrade_effects(slot.option, build.ship).get("extra_upgrade_slots", 0)
                or 0
            ),
        )
        for slot in upgrade_slots
    )
    access = calculate_upgrade_slot_access(
        ship_upgrade_slots=build.ship.upgrade_slots,
        unlock_effect_slots=unlock_effect_slots,
        research_upgrade_slots=build.research_upgrade_slots,
    )
    weapon_total = sum(
        int(slot.quantity or 1) for slot in build.slots if slot.slot_type.startswith("weapon_")
    )
    metrics = BuildListMetrics(
        crew_total=build.sailors + build.soldiers + build.musketeers + build.mercenaries,
        crew_capacity=build.ship.crew_capacity,
        upgrade_slots_used=len(upgrade_slots),
        upgrade_slots_available=access.available_slots,
        weapon_total=weapon_total,
        special_crew_total=sum(1 for slot in build.slots if slot.slot_type == "special_crew"),
        ammunition_slots_used=sum(1 for slot in build.slots if slot.slot_type == "ammunition"),
        consumable_slots_used=sum(1 for slot in build.slots if slot.slot_type == "consumable"),
        hold_slots_used=sum(1 for slot in build.slots if slot.slot_type == "hold"),
    )
    return BuildSummaryRead(
        id=build.id,
        owner_id=build.owner_id,
        is_official_template=build.is_official_template,
        build_name=build.build_name,
        build_type=build.build_type,
        classification_tags=build.classification_tags,
        build_role_label=build.build_role_label,
        upvote_count=build.upvote_count,
        has_upvoted=build.has_upvoted,
        ship=ShipRead.model_validate(build.ship),
        metrics=metrics,
        ammunition_slots=build.ammunition_slots,
        hold_slots=build.hold_slots,
        created_at=build.created_at,
        updated_at=build.updated_at,
    )


def list_build_page(
    db: Session,
    *,
    search: str | None = None,
    build_type: str | None = None,
    classification: str | None = None,
    owner_id: int | None = None,
    viewer_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> BuildPage:
    items = list_builds(
        db,
        search=search,
        build_type=build_type,
        classification=classification,
        owner_id=owner_id,
        viewer_id=viewer_id,
        limit=limit,
        offset=offset,
    )
    count_statement = _apply_build_filters(
        select(func.count(Build.id)).join(Build.ship),
        search=search,
        build_type=build_type,
        classification=classification,
        owner_id=owner_id,
    )
    total = int(db.scalar(count_statement) or 0)
    return BuildPage(
        items=[_summary_for_build(build) for build in items],
        total=total,
        limit=limit,
        offset=offset,
    )


def list_user_build_page(
    db: Session,
    user_id: int,
    *,
    search: str | None = None,
    build_type: str | None = None,
    classification: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> BuildPage:
    return list_build_page(
        db,
        search=search,
        build_type=build_type,
        classification=classification,
        owner_id=user_id,
        viewer_id=user_id,
        limit=limit,
        offset=offset,
    )


def list_builds(
    db: Session,
    search: str | None = None,
    build_type: str | None = None,
    classification: str | None = None,
    owner_id: int | None = None,
    viewer_id: int | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[Build]:
    vote_count = (
        select(func.count(BuildVote.id))
        .where(BuildVote.build_id == Build.id)
        .correlate(Build)
        .scalar_subquery()
    )
    statement = (
        _build_query()
        .join(Build.ship)
        .order_by(
            vote_count.desc(),
            Build.created_at.desc(),
            Build.id.desc(),
        )
    )
    statement = _apply_build_filters(
        statement,
        search=search,
        build_type=build_type,
        classification=classification,
        owner_id=owner_id,
    )
    if offset:
        statement = statement.offset(offset)
    if limit is not None:
        statement = statement.limit(limit)
    rows = list(db.scalars(statement).unique().all())
    return _decorate_builds(db, rows, viewer_id)


def get_build(db: Session, build_id: int, viewer_id: int | None = None) -> Build | None:
    build = db.scalar(_build_query().where(Build.id == build_id))
    if build is None:
        return None
    build.printout_url = public_printout_url(build.id) if build.printout_checksum else None
    return _decorate_builds(db, [build], viewer_id)[0]


def _apply_build_payload(
    db_build: Build,
    build: BuildCreate,
    slots: list[BuildSlot],
    research_feature: BuildFeatureDefinition | None,
) -> None:
    db_build.build_name = build.build_name
    db_build.build_type = build.build_type
    db_build.ship_id = build.ship_id
    db_build.research_upgrade_feature = research_feature
    db_build.mortar_modification_installed = build.mortar_modification_installed
    db_build.sailors = build.sailors
    db_build.soldiers = build.soldiers
    db_build.musketeers = build.musketeers
    db_build.mercenaries = build.mercenaries
    db_build.details = build.details
    db_build.slots = slots
    db_build.classifications = [BuildClassification(tag=tag) for tag in build.classification_tags]


def create_build(db: Session, build: BuildCreate, owner_id: int | None = None) -> Build:
    _, slots, research_feature = validate_and_prepare_build(db, build)
    db_build = Build(owner_id=owner_id)
    _apply_build_payload(db_build, build, slots, research_feature)
    db.add(db_build)
    db.commit()
    return get_build(db, db_build.id, viewer_id=owner_id) or db_build


def update_user_build(db: Session, build_id: int, user_id: int, build: BuildCreate) -> Build | None:
    db_build = get_build(db, build_id)
    if db_build is None or db_build.owner_id != user_id or db_build.is_official_template:
        return None

    _, slots, research_feature = validate_and_prepare_build(db, build)
    db_build.slots.clear()
    db.flush()
    _apply_build_payload(db_build, build, slots, research_feature)
    db.add(db_build)
    db.commit()
    return get_build(db, db_build.id, viewer_id=user_id) or db_build


def delete_build(db: Session, build_id: int) -> bool:
    build = get_build(db, build_id)
    if build is None:
        return False
    delete_build_and_files(db, build)
    return True


def list_user_builds(
    db: Session,
    user_id: int,
    search: str | None = None,
    build_type: str | None = None,
    classification: str | None = None,
) -> list[Build]:
    return list_builds(
        db,
        search=search,
        build_type=build_type,
        classification=classification,
        owner_id=user_id,
        viewer_id=user_id,
    )


def delete_user_build(db: Session, build_id: int, user_id: int) -> bool:
    build = get_build(db, build_id)
    if build is None or build.owner_id != user_id:
        return False
    delete_build_and_files(db, build)
    return True
