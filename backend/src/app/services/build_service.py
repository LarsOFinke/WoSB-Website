from collections.abc import Iterable
import json

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Build, BuildItemCategory, BuildItemOption, BuildSlot, Ship
from app.models.build import WEAPON_SLOT_TYPE_BY_ARC
from app.schemas import BuildCreate
from app.schemas.build import BUILD_TYPE_VALUES, InventorySlot, WEAPON_ARC_KEYS


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

UPGRADE_SLOT_LIMIT = 6
BASE_UPGRADE_SLOT_LIMIT = 4
UNLOCKABLE_UPGRADE_SLOT = 5
SHIP_EXTRA_UPGRADE_SLOT = 6
CONSUMABLE_SLOT_LIMIT = 3
SPECIAL_CREW_SLOT_LIMIT = 8
WEAPON_ARC_SLOT_LIMIT = 12


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


def _option_effects(option: BuildItemOption) -> dict[str, int | float]:
    if not option.stat_effects:
        return {}
    try:
        payload = json.loads(option.stat_effects)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return {str(key): value for key, value in payload.items() if isinstance(value, (int, float))}


def _selected_upgrade_options(
    option_map: dict[tuple[str, str], BuildItemOption], build: BuildCreate
) -> dict[int, BuildItemOption]:
    selected: dict[int, BuildItemOption] = {}
    for index in range(1, UPGRADE_SLOT_LIMIT + 1):
        name = _normalize_name(getattr(build, f"upgrade_{index}"))
        if not name:
            continue
        selected[index] = _require_option(option_map, name, "upgrade", f"Upgrade {index}")
    return selected


def _upgrade_access(ship: Ship, selected_upgrades: dict[int, BuildItemOption]) -> dict[str, int | bool]:
    """Return slot access flags for the six-slot Build Manager.

    Slots 1-4 are normal ship upgrade slots. Slot 5 is unlocked by an
    expansion upgrade selected in one of those normal slots. Slot 6 is not
    unlocked by upgrades; it is a ship-specific extra slot represented by
    ``Ship.upgrade_slots >= 6`` in the catalog.
    """

    base_slots = min(max(int(ship.upgrade_slots or 0), 0), BASE_UPGRADE_SLOT_LIMIT)
    unlock_effect_slots = 0
    for index, option in selected_upgrades.items():
        if index > BASE_UPGRADE_SLOT_LIMIT:
            continue
        unlock_effect_slots += int(_option_effects(option).get("extra_upgrade_slots", 0))

    slot_5_supported = int(ship.upgrade_slots or 0) >= UNLOCKABLE_UPGRADE_SLOT
    slot_5_unlocked = slot_5_supported and unlock_effect_slots > 0
    slot_6_available = int(ship.upgrade_slots or 0) >= SHIP_EXTRA_UPGRADE_SLOT

    return {
        "base_slots": base_slots,
        "slot_5_unlocked": slot_5_unlocked,
        "slot_6_available": slot_6_available,
        "unlock_effect_slots": max(unlock_effect_slots, 0),
        "ship_extra_slots": 1 if slot_6_available else 0,
        "available_slots": min(
            UPGRADE_SLOT_LIMIT,
            base_slots + (1 if slot_5_unlocked else 0) + (1 if slot_6_available else 0),
        ),
    }


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
        build.upgrade_6,
    ):
        normalized = _normalize_name(value)
        if normalized:
            names.append(normalized)

    for arc in WEAPON_ARC_KEYS:
        names.extend(slot.item for slot in getattr(build, f"{arc}_weapon_slots"))
    for slots in (
        build.special_crew_slots,
        build.ammunition_slots,
        build.consumable_slots,
        build.hold_slots,
    ):
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

    for index, option in _selected_upgrade_options(option_map, build).items():
        slots.append(BuildSlot(slot_type="upgrade", slot_index=index, option_id=option.id))

    for arc in WEAPON_ARC_KEYS:
        form_slots = getattr(build, f"{arc}_weapon_slots")
        for index, slot in enumerate(form_slots, start=1):
            option = _require_option(option_map, slot.item, "weapon", f"{arc.title()} weapon")
            slots.append(
                BuildSlot(
                    slot_type=WEAPON_SLOT_TYPE_BY_ARC[arc],
                    slot_index=index,
                    option_id=option.id,
                    quantity=slot.quantity,
                )
            )

    for index, slot in enumerate(build.special_crew_slots, start=1):
        option = _require_option(option_map, slot.item, "special_crew", "Special crew")
        slots.append(
            BuildSlot(
                slot_type="special_crew",
                slot_index=index,
                option_id=option.id,
                quantity=slot.quantity,
            )
        )

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

    option_map = _load_option_map(db, _selected_item_names(build))
    selected_upgrades = _selected_upgrade_options(option_map, build)
    upgrade_access = _upgrade_access(ship, selected_upgrades)

    if _normalize_name(build.upgrade_5) and not bool(upgrade_access["slot_5_unlocked"]):
        raise BuildValidationError(
            "Upgrade slot 5 is locked. Select an unlock upgrade in slots 1-4 first."
        )
    if _normalize_name(build.upgrade_6) and not bool(upgrade_access["slot_6_available"]):
        raise BuildValidationError(
            "Upgrade slot 6 is only available on ships with an extra upgrade slot."
        )

    total_effects: dict[str, int | float] = {}
    for option in selected_upgrades.values():
        for key, value in _option_effects(option).items():
            total_effects[key] = total_effects.get(key, 0) + value

    effective_crew_capacity = max(0, ship.crew_capacity + int(total_effects.get("crew_capacity", 0)))
    effective_sailor_minimum = max(0, ship.sailor_minimum + int(total_effects.get("sailor_minimum", 0)))
    crew_total = _crew_total(build)
    if build.sailors < effective_sailor_minimum:
        raise BuildValidationError(f"This ship requires at least {effective_sailor_minimum} sailors after upgrade modifiers.")
    if crew_total > effective_crew_capacity:
        raise BuildValidationError(
            f"The crew distribution ({crew_total}) exceeds the effective ship capacity ({effective_crew_capacity})."
        )

    for arc in WEAPON_ARC_KEYS:
        arc_slots = getattr(build, f"{arc}_weapon_slots")
        _validate_unique_slots(arc_slots, f"{arc.title()} weapons")
        if len(arc_slots) > WEAPON_ARC_SLOT_LIMIT:
            raise BuildValidationError(f"{arc.title()} weapons are limited to {WEAPON_ARC_SLOT_LIMIT} slots.")
    _validate_unique_slots(build.special_crew_slots, "Special crew")
    _validate_unique_slots(build.ammunition_slots, "Ammunition")
    _validate_unique_slots(build.consumable_slots, "Consumables")
    _validate_unique_slots(build.hold_slots, "Hold")
    if len(build.special_crew_slots) > SPECIAL_CREW_SLOT_LIMIT:
        raise BuildValidationError(f"Special crew is limited to {SPECIAL_CREW_SLOT_LIMIT} slots.")
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
