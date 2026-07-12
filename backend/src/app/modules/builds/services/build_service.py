from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.builds.models.build import Build
from app.modules.builds.models.build_item_category import BuildItemCategory
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.builds.models.build_slot import BuildSlot
from app.modules.ships.models.ship import Ship
from app.modules.ships.services.weapon_compatibility import is_weapon_compatible
from app.modules.builds.schemas.build_create import BuildCreate
from app.modules.builds.schemas.constants import BUILD_TYPE_VALUES
from app.modules.builds.schemas.inventory_slot import InventorySlot
from app.modules.builds.services.build_limits import (
    BASE_UPGRADE_SLOT_LIMIT,
    CONSUMABLE_SLOT_LIMIT,
    DEDICATED_WEAPON_ROW_LIMIT,
    SPECIAL_CREW_SLOT_LIMIT,
    UPGRADE_SLOT_LIMIT,
    WEAPON_ARC_ROW_LIMIT,
)
from app.modules.builds.services.upgrade_slot_service import calculate_upgrade_slot_access
from app.modules.builds.services.research_upgrade_reward import research_upgrade_slot_effects
from app.modules.builds.services.specialist_effect_service import resolve_specialist_effects
from app.modules.builds.services.ship_upgrade_effect_service import effective_upgrade_effects
from app.modules.builds.services.build_stat_service import apply_percentage_effects


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

WEAPON_SLOT_TYPE_BY_FIELD = {
    "front_weapon_slots": "weapon_front",
    "rear_weapon_slots": "weapon_rear",
    "port_weapon_slots": "weapon_port",
    "starboard_weapon_slots": "weapon_starboard",
    "mortar_weapon_slots": "weapon_mortar",
    "special_weapon_slots": "weapon_special",
}
WEAPON_FIELD_LABELS = {
    "front_weapon_slots": "Front weapons",
    "rear_weapon_slots": "Rear weapons",
    "port_weapon_slots": "Port weapons",
    "starboard_weapon_slots": "Starboard weapons",
    "mortar_weapon_slots": "Mortars",
    "special_weapon_slots": "Special weapons",
}


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
        .options(selectinload(BuildItemOption.effects))
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


def _option_effects(option: BuildItemOption, ship: Ship | None = None) -> dict[str, int | float]:
    return effective_upgrade_effects(option, ship)


def _sum_effects(options: Iterable[BuildItemOption], ship: Ship | None = None) -> dict[str, int | float]:
    totals: dict[str, int | float] = {}
    for option in options:
        for key, value in _option_effects(option, ship).items():
            totals[key] = totals.get(key, 0) + value
    return totals


def _selected_upgrade_options(
    option_map: dict[tuple[str, str], BuildItemOption], build: BuildCreate
) -> dict[int, BuildItemOption]:
    selected: dict[int, BuildItemOption] = {}
    selected_names: set[str] = set()
    for index in range(1, UPGRADE_SLOT_LIMIT + 1):
        name = _normalize_name(getattr(build, f"upgrade_{index}"))
        if not name:
            continue
        normalized = name.casefold()
        if normalized in selected_names:
            raise BuildValidationError("Upgrades: each upgrade can only be selected once.")
        selected_names.add(normalized)
        selected[index] = _require_option(option_map, name, "upgrade", f"Upgrade {index}")
    return selected


def _selected_special_crew_options(
    option_map: dict[tuple[str, str], BuildItemOption], build: BuildCreate
) -> list[tuple[BuildItemOption, int]]:
    return [
        (
            _require_option(option_map, slot.item, "special_crew", "Special crew"),
            1,
        )
        for slot in build.special_crew_slots
    ]



def _upgrade_access(
    ship: Ship,
    selected_upgrades: dict[int, BuildItemOption],
    *,
    research_upgrade_slot_unlocked: bool,
) -> dict[str, int | bool]:
    # Expansion upgrades may only unlock slots when they are installed in a
    # position already available without their own effect. This prevents a
    # locked expansion position from unlocking itself while still allowing
    # Structural Expansion in a research or ship-extra position.
    pre_expansion_access = calculate_upgrade_slot_access(
        ship_upgrade_slots=int(ship.upgrade_slots or 0),
        unlock_effect_slots=0,
        research_upgrade_slot_unlocked=research_upgrade_slot_unlocked,
    )
    unlock_effect_slots = 0
    for index, option in selected_upgrades.items():
        if index > pre_expansion_access.available_slots:
            continue
        gross_slots = max(
            0,
            int(_option_effects(option, ship).get("extra_upgrade_slots", 0) or 0),
        )
        if gross_slots > 0:
            # Use the full tooltip value. The upgrade's own occupied position
            # is already represented by the selected build slot.
            unlock_effect_slots += gross_slots

    access = calculate_upgrade_slot_access(
        ship_upgrade_slots=int(ship.upgrade_slots or 0),
        unlock_effect_slots=unlock_effect_slots,
        research_upgrade_slot_unlocked=research_upgrade_slot_unlocked,
    )
    return {
        "base_slots": access.base_slots,
        "slot_5_unlocked": access.slot_5_unlocked,
        "slot_6_available": access.slot_6_available,
        "slot_7_available": access.slot_7_available,
        "slot_8_available": access.slot_8_available,
        "unlock_effect_slots": access.unlock_effect_slots,
        "research_slots": access.research_slots,
        "ship_extra_slots": access.ship_extra_slots,
        "available_slots": access.available_slots,
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
        build.upgrade_7,
        build.upgrade_8,
    ):
        normalized = _normalize_name(value)
        if normalized:
            names.append(normalized)

    for field_name in WEAPON_SLOT_TYPE_BY_FIELD:
        names.extend(slot.item for slot in getattr(build, field_name))
    for slots in (
        build.special_crew_slots,
        build.ammunition_slots,
        build.consumable_slots,
        build.hold_slots,
    ):
        names.extend(slot.item for slot in slots)
    return names


def _weapon_capacity_by_field(ship: Ship) -> dict[str, int]:
    return {
        "front_weapon_slots": int(ship.front_weapon_capacity or 0),
        "rear_weapon_slots": int(ship.rear_weapon_capacity or 0),
        "port_weapon_slots": int(ship.broadside_weapon_capacity or 0),
        "starboard_weapon_slots": int(ship.broadside_weapon_capacity or 0),
        "mortar_weapon_slots": int(ship.mortar_weapon_capacity or 0),
        "special_weapon_slots": int(ship.special_weapon_capacity or 0),
    }


def _validate_weapon_loadout(
    ship: Ship,
    build: BuildCreate,
    option_map: dict[tuple[str, str], BuildItemOption],
) -> None:
    capacities = _weapon_capacity_by_field(ship)
    for field_name, slot_type in WEAPON_SLOT_TYPE_BY_FIELD.items():
        slots = getattr(build, field_name)
        label = WEAPON_FIELD_LABELS[field_name]
        _validate_unique_slots(slots, label)
        field_limit = (
            DEDICATED_WEAPON_ROW_LIMIT
            if field_name in {"mortar_weapon_slots", "special_weapon_slots"}
            else WEAPON_ARC_ROW_LIMIT
        )
        if len(slots) > field_limit:
            raise BuildValidationError(f"{label} are limited to {field_limit} item rows.")

        capacity = capacities[field_name]
        quantity_total = sum(slot.quantity or 1 for slot in slots)
        if quantity_total > capacity:
            raise BuildValidationError(
                f"{label}: selected quantity ({quantity_total}) exceeds this ship's capacity ({capacity})."
            )
        if quantity_total > 0 and capacity <= 0:
            raise BuildValidationError(f"{label}: this ship has no valid slots for that weapon position.")

        for slot in slots:
            option = _require_option(option_map, slot.item, "weapon", label)
            allowed_slots = option.allowed_slots
            if slot_type not in allowed_slots:
                raise BuildValidationError(f"{label}: '{slot.item}' cannot be mounted in this slot type.")
            mount = ship._mount(slot_type)
            if mount is None or not is_weapon_compatible(option, mount):
                raise BuildValidationError(
                    f"{label}: '{slot.item}' is not compatible with this ship's mount profile."
                )
            if slot_type == "weapon_mortar":
                max_caliber = ship.max_mortar_caliber_inches
                if option.option_kind not in {"mortar", "mortar_launcher"}:
                    raise BuildValidationError(f"{label}: '{slot.item}' is not a mortar-slot weapon.")
                if max_caliber is not None and option.weapon_caliber_inches is not None and option.weapon_caliber_inches > float(max_caliber):
                    raise BuildValidationError(
                        f"{label}: '{slot.item}' exceeds this ship's mortar caliber limit ({max_caliber} in)."
                    )
            elif slot_type == "weapon_special":
                if option.option_kind != "special_weapon":
                    raise BuildValidationError(f"{label}: '{slot.item}' is not a special weapon.")
            elif option.option_kind in {"mortar", "mortar_launcher", "special_weapon"}:
                raise BuildValidationError(f"{label}: '{slot.item}' must be placed in its dedicated slot.")


def _build_slots(
    db: Session,
    build: BuildCreate,
    option_map: dict[tuple[str, str], BuildItemOption] | None = None,
) -> list[BuildSlot]:
    option_map = option_map or _load_option_map(db, _selected_item_names(build))
    slots: list[BuildSlot] = []

    if build.sails:
        option = _require_option(option_map, build.sails, "sail", "Sail")
        slots.append(BuildSlot(slot_type="sail", slot_index=1, option_id=option.id))

    if build.lantern:
        option = _require_option(option_map, build.lantern, "lantern", "Lantern")
        slots.append(BuildSlot(slot_type="lantern", slot_index=1, option_id=option.id))

    for index, option in _selected_upgrade_options(option_map, build).items():
        slots.append(BuildSlot(slot_type="upgrade", slot_index=index, option_id=option.id))

    for field_name, slot_type in WEAPON_SLOT_TYPE_BY_FIELD.items():
        form_slots = getattr(build, field_name)
        for index, slot in enumerate(form_slots, start=1):
            option = _require_option(option_map, slot.item, "weapon", WEAPON_FIELD_LABELS[field_name])
            slots.append(
                BuildSlot(
                    slot_type=slot_type,
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
                quantity=1,
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


def _validate_and_prepare_build(db: Session, build: BuildCreate) -> tuple[Ship, list[BuildSlot]]:
    """Validate a complete build payload and materialize its normalized slots.

    Create and update use this exact boundary so interactive editing cannot drift
    from initial build creation.
    """

    ship = db.get(Ship, build.ship_id)
    if ship is None or not ship.is_active:
        raise BuildValidationError("The selected ship does not exist.")

    option_map = _load_option_map(db, _selected_item_names(build))
    selected_upgrades = _selected_upgrade_options(option_map, build)
    selected_special_crew = _selected_special_crew_options(option_map, build)
    upgrade_access = _upgrade_access(
        ship,
        selected_upgrades,
        research_upgrade_slot_unlocked=build.research_upgrade_slot_unlocked,
    )

    if _normalize_name(build.upgrade_5) and not bool(upgrade_access["slot_5_unlocked"]):
        raise BuildValidationError(
            "Upgrade slot 5 is locked. Enable the ship-line research reward or select an expansion upgrade in slots 1-4."
        )
    if _normalize_name(build.upgrade_6) and not bool(upgrade_access["slot_6_available"]):
        raise BuildValidationError(
            "Upgrade slot 6 requires Structural Expansion or two one-slot sources."
        )
    if _normalize_name(build.upgrade_7) and not bool(upgrade_access["slot_7_available"]):
        raise BuildValidationError(
            "Upgrade slot 7 requires Structural Expansion plus either the research reward or a ship-specific extra slot."
        )
    if _normalize_name(build.upgrade_8) and not bool(upgrade_access["slot_8_available"]):
        raise BuildValidationError(
            "Upgrade slot 8 requires Structural Expansion, the research reward, and a ship-specific extra slot."
        )

    selected_equipment: list[BuildItemOption] = []
    if build.sails:
        selected_equipment.append(_require_option(option_map, build.sails, "sail", "Sail"))
    if build.lantern:
        selected_equipment.append(_require_option(option_map, build.lantern, "lantern", "Lantern"))
    equipment_effect_sets = [_option_effects(option, ship) for option in selected_equipment]
    upgrade_effect_sets = [
        _option_effects(option, ship) for option in selected_upgrades.values()
    ]
    specialist_effect_sets = [
        resolve_specialist_effects(
            [(_option_effects(option, ship), quantity)],
            sailors=build.sailors,
            soldiers=build.soldiers,
            musketeers=build.musketeers,
            mercenaries=build.mercenaries,
        )
        for option, quantity in selected_special_crew
    ]
    research_effects = research_upgrade_slot_effects(build.research_upgrade_slot_unlocked)
    effect_sets = [
        *equipment_effect_sets,
        *upgrade_effect_sets,
        *specialist_effect_sets,
        *([research_effects] if research_effects else []),
    ]
    total_effects: dict[str, int | float] = {}
    for effect_set in effect_sets:
        for key, value in effect_set.items():
            total_effects[key] = total_effects.get(key, 0) + value

    effective_crew_capacity = max(
        0,
        round(
            apply_percentage_effects(
                ship.crew_capacity,
                "crew_capacity_pct",
                effect_sets,
                fallback_total=float(total_effects.get("crew_capacity_pct", 0) or 0),
            )
            + float(total_effects.get("crew_capacity", 0) or 0)
        ),
    )
    effective_sailor_minimum = max(
        0, ship.sailor_minimum + int(total_effects.get("sailor_minimum", 0) or 0)
    )
    if build.sailors < effective_sailor_minimum:
        raise BuildValidationError(
            f"Sailors ({build.sailors}) are below this build's required minimum ({effective_sailor_minimum})."
        )

    crew_total = _crew_total(build)
    if crew_total > effective_crew_capacity:
        raise BuildValidationError(
            f"The crew distribution ({crew_total}) exceeds the effective ship capacity ({effective_crew_capacity})."
        )

    _validate_weapon_loadout(ship, build, option_map)
    _validate_unique_slots(build.special_crew_slots, "Special crew")
    _validate_unique_slots(build.ammunition_slots, "Ammunition")
    _validate_unique_slots(build.consumable_slots, "Consumables")
    _validate_unique_slots(build.hold_slots, "Hold")
    if len(build.special_crew_slots) > SPECIAL_CREW_SLOT_LIMIT:
        raise BuildValidationError(
            f"Special crew is limited to {SPECIAL_CREW_SLOT_LIMIT} distinct specialists."
        )
    if len(build.consumable_slots) > CONSUMABLE_SLOT_LIMIT:
        raise BuildValidationError(f"Consumables are limited to {CONSUMABLE_SLOT_LIMIT} slots.")

    return ship, _build_slots(db, build, option_map)


def _apply_build_payload(db_build: Build, build: BuildCreate, slots: list[BuildSlot]) -> None:
    db_build.build_name = build.build_name
    db_build.build_type = build.build_type
    db_build.ship_id = build.ship_id
    db_build.research_upgrade_slot_unlocked = build.research_upgrade_slot_unlocked
    db_build.sailors = build.sailors
    db_build.soldiers = build.soldiers
    db_build.musketeers = build.musketeers
    db_build.mercenaries = build.mercenaries
    db_build.details = build.details
    db_build.slots = slots


def create_build(db: Session, build: BuildCreate, owner_id: int | None = None) -> Build:
    _, slots = _validate_and_prepare_build(db, build)
    db_build = Build(owner_id=owner_id)
    _apply_build_payload(db_build, build, slots)
    db.add(db_build)
    db.commit()
    return get_build(db, db_build.id) or db_build


def update_user_build(
    db: Session, build_id: int, user_id: int, build: BuildCreate
) -> Build | None:
    db_build = get_build(db, build_id)
    if db_build is None or db_build.owner_id != user_id or db_build.is_official_template:
        return None

    _, slots = _validate_and_prepare_build(db, build)
    db_build.slots.clear()
    db.flush()
    _apply_build_payload(db_build, build, slots)
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
