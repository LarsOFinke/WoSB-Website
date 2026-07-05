from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Build, BuildItemCategory, BuildItemOption, BuildSlot, Ship
from app.schemas import BuildCreate
from app.schemas.build import BUILD_TYPE_VALUES, InventorySlot


class BuildValidationError(ValueError):
    pass


SINGLE_SLOT_MAP = {
    "sail": "sail",
    "lantern": "lantern",
}

INVENTORY_SLOT_MAP = {
    "ammunition": "ammunition",
    "consumable": "consumable",
    "hold": "hold",
}

UPGRADE_SLOT_LIMIT = 5
CONSUMABLE_SLOT_LIMIT = 3


def _crew_total(build: BuildCreate) -> int:
    return build.sailors + build.soldiers + build.musketeers + build.mercenaries


def _normalize_name(value: str | None) -> str | None:
    if not value:
        return None
    stripped = value.strip()
    return stripped or None


def _validate_unique_slots(slots: list[InventorySlot], label: str) -> None:
    normalized = [slot.item.casefold() for slot in slots]
    if len(normalized) != len(set(normalized)):
        raise BuildValidationError(
            f"{label}: an item can only be selected once. Same items stack in one inventory slot."
        )


def _load_option_map(db: Session, names: Iterable[str]) -> dict[tuple[str, str], BuildItemOption]:
    cleaned_names = {name.strip() for name in names if name and name.strip()}
    if not cleaned_names:
        return {}
    options = db.scalars(
        select(BuildItemOption)
        .join(BuildItemOption.category)
        .where(
            BuildItemOption.name.in_(cleaned_names),
            BuildItemOption.is_active.is_(True),
            BuildItemCategory.is_active.is_(True),
        )
    ).unique().all()
    return {(option.category.key, option.name.casefold()): option for option in options}


def _require_option(
    option_map: dict[tuple[str, str], BuildItemOption], name: str, expected_category: str, label: str
) -> BuildItemOption:
    option = option_map.get((expected_category, name.casefold()))
    if option is None:
        raise BuildValidationError(f"{label}: '{name}' is not a valid option.")
    return option


def _selected_item_names(build: BuildCreate) -> list[str]:
    names: list[str] = []
    for value in (
        build.sails,
        build.lantern,
        build.upgrade_1,
        build.upgrade_2,
        build.upgrade_3,
        build.upgrade_4,
        build.upgrade_5,
    ):
        normalized = _normalize_name(value)
        if normalized:
            names.append(normalized)

    for slots in (build.ammunition_slots, build.consumable_slots, build.hold_slots):
        names.extend(slot.item for slot in slots)
    return names


def _build_slots(db: Session, build: BuildCreate) -> list[BuildSlot]:
    option_map = _load_option_map(db, _selected_item_names(build))
    slots: list[BuildSlot] = []

    if build.sails:
        option = _require_option(option_map, build.sails, "sail", "Sail")
        slots.append(BuildSlot(slot_type="sail", slot_index=1, option_id=option.id))

    if build.lantern:
        option = _require_option(option_map, build.lantern, "lantern", "Lantern")
        slots.append(BuildSlot(slot_type="lantern", slot_index=1, option_id=option.id))

    for index in range(1, UPGRADE_SLOT_LIMIT + 1):
        name = _normalize_name(getattr(build, f"upgrade_{index}"))
        if not name:
            continue
        option = _require_option(option_map, name, "upgrade", f"Upgrade {index}")
        slots.append(BuildSlot(slot_type="upgrade", slot_index=index, option_id=option.id))

    for slot_type, category_key in INVENTORY_SLOT_MAP.items():
        form_slots = getattr(build, f"{slot_type}_slots")
        for index, slot in enumerate(form_slots, start=1):
            option = _require_option(option_map, slot.item, category_key, slot_type.title())
            slots.append(
                BuildSlot(
                    slot_type=slot_type,
                    slot_index=index,
                    option_id=option.id,
                    quantity=slot.quantity,
                )
            )

    return slots


def _build_query():
    return select(Build).options(selectinload(Build.slots).selectinload(BuildSlot.option))


def list_builds(
    db: Session,
    search: str | None = None,
    build_type: str | None = None,
    owner_id: int | None = None,
) -> list[Build]:
    statement = _build_query().join(Build.ship).order_by(Build.created_at.desc(), Build.id.desc())
    if search:
        like = f"%{search.strip()}%"
        statement = statement.where(
            Build.build_name.ilike(like)
            | Ship.name.ilike(like)
            | Build.build_type.ilike(like)
        )
    if build_type:
        normalized_type = build_type.strip().lower()
        if normalized_type in BUILD_TYPE_VALUES:
            statement = statement.where(Build.build_type == normalized_type)
    if owner_id is not None:
        statement = statement.where(Build.owner_id == owner_id)
    return list(db.scalars(statement).unique().all())


def get_build(db: Session, build_id: int) -> Build | None:
    return db.scalar(_build_query().where(Build.id == build_id))


def create_build(db: Session, build: BuildCreate, owner_id: int | None = None) -> Build:
    ship = db.get(Ship, build.ship_id)
    if ship is None or not ship.is_active:
        raise BuildValidationError("The selected ship does not exist.")

    crew_total = _crew_total(build)
    if build.sailors < ship.sailor_minimum:
        raise BuildValidationError(f"This ship requires at least {ship.sailor_minimum} sailors.")
    if crew_total > ship.crew_capacity:
        raise BuildValidationError(
            f"The crew distribution ({crew_total}) exceeds the ship capacity ({ship.crew_capacity})."
        )


    _validate_unique_slots(build.ammunition_slots, "Ammunition")
    _validate_unique_slots(build.consumable_slots, "Consumables")
    _validate_unique_slots(build.hold_slots, "Hold")
    if len(build.consumable_slots) > CONSUMABLE_SLOT_LIMIT:
        raise BuildValidationError(f"Consumables are limited to {CONSUMABLE_SLOT_LIMIT} slots.")

    db_build = Build(
        build_name=build.build_name,
        build_type=build.build_type,
        ship_id=build.ship_id,
        owner_id=owner_id,
        sailors=build.sailors,
        soldiers=build.soldiers,
        musketeers=build.musketeers,
        mercenaries=build.mercenaries,
        details=build.details,
    )
    db_build.slots = _build_slots(db, build)
    db.add(db_build)
    db.commit()
    return get_build(db, db_build.id) or db_build


def delete_build(db: Session, build_id: int) -> bool:
    build = get_build(db, build_id)
    if build is None:
        return False
    db.delete(build)
    db.commit()
    return True

def list_user_builds(
    db: Session,
    user_id: int,
    search: str | None = None,
    build_type: str | None = None,
) -> list[Build]:
    return list_builds(db, search=search, build_type=build_type, owner_id=user_id)


def delete_user_build(db: Session, build_id: int, user_id: int) -> bool:
    build = get_build(db, build_id)
    if build is None or build.owner_id != user_id:
        return False
    db.delete(build)
    db.commit()
    return True

