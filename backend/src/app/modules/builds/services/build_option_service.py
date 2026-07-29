from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.builds.models.build_item_category import BuildItemCategory
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.builds.schemas.build_item_category_read import BuildItemCategoryRead
from app.modules.builds.schemas.build_item_option_read import BuildItemOptionRead
from app.modules.builds.schemas.build_options_catalog import BuildOptionsCatalog
from app.modules.builds.schemas.build_role import BuildRoleRead
from app.modules.builds.services.build_role_service import list_build_roles
from app.modules.builds.services.build_limits import build_limits_for_api
from app.modules.builds.services.build_stat_service import stat_definitions_for_api
from app.modules.builds.services.research_upgrade_reward import RESEARCH_UPGRADE_SLOT_EFFECTS
from app.modules.builds.services.ship_upgrade_effect_service import (
    effective_upgrade_effects,
    has_ship_upgrade_override,
)
from app.modules.ships.models.ship import Ship
from app.modules.ships.models.ship_upgrade_effect import ShipUpgradeEffectOverride
from app.modules.ships.models.weapon_mount import ShipWeaponMount
from app.modules.ships.services.weapon_compatibility import is_weapon_compatible


def list_build_options(db: Session, ship_id: int | None = None) -> BuildOptionsCatalog:
    categories = list(
        db.scalars(
            select(BuildItemCategory)
            .where(BuildItemCategory.is_active.is_(True))
            .order_by(BuildItemCategory.sort_order, BuildItemCategory.label)
        ).all()
    )
    options = list(
        db.scalars(
            select(BuildItemOption)
            .options(
                selectinload(BuildItemOption.effects),
                selectinload(BuildItemOption.slot_type_links),
            )
            .join(BuildItemOption.category)
            .where(BuildItemOption.is_active.is_(True), BuildItemCategory.is_active.is_(True))
            .order_by(BuildItemCategory.sort_order, func.lower(BuildItemOption.name))
        ).unique().all()
    )

    ship = None
    if ship_id is not None:
        ship = db.scalar(
            select(Ship)
            .options(
                selectinload(Ship.weapon_mounts).selectinload(ShipWeaponMount.slot_type),
                selectinload(Ship.weapon_mounts).selectinload(ShipWeaponMount.max_weapon_class),
                selectinload(Ship.upgrade_effect_overrides)
                .selectinload(ShipUpgradeEffectOverride.option)
                .selectinload(BuildItemOption.effects),
            )
            .where(Ship.id == ship_id, Ship.is_active.is_(True))
        )

    grouped: dict[str, list[BuildItemOptionRead]] = {category.key: [] for category in categories}
    for option in options:
        if option.category.key == "weapon" and ship_id is not None:
            if ship is None:
                continue
            allowed_slot_types: list[str] = []
            for mount in ship.weapon_mounts:
                is_modifier_mortar = (
                    mount.slot_type.code == "weapon_mortar"
                    and ship.mortar_modification is not None
                )
                if is_weapon_compatible(
                    option,
                    mount,
                    capacity_override=(
                        ship.effective_weapon_capacity(
                            "weapon_mortar",
                            mortar_modification_installed=True,
                        )
                        if is_modifier_mortar
                        else None
                    ),
                    max_caliber_override=(
                        ship.effective_max_mortar_caliber_inches(
                            mortar_modification_installed=True
                        )
                        if is_modifier_mortar
                        else None
                    ),
                ):
                    allowed_slot_types.append(mount.slot_type.code)
            allowed_slot_types.sort()
            if not allowed_slot_types:
                continue
        else:
            allowed_slot_types = option.allowed_slots
        grouped.setdefault(option.category.key, []).append(
            BuildItemOptionRead(
                id=option.id,
                category_key=option.category.key,
                name=option.name,
                source=option.source,
                notes=option.notes,
                image_url=option.image_url,
                option_kind=option.option_kind,
                allowed_slot_types=allowed_slot_types,
                weapon_class=option.weapon_class_code,
                weapon_caliber_inches=option.weapon_caliber_inches,
                stat_effects=effective_upgrade_effects(option, ship),
                base_stat_effects=option.stat_effects,
                is_ship_specific=has_ship_upgrade_override(option, ship),
                sort_order=option.sort_order,
                created_at=option.created_at,
                updated_at=option.updated_at,
            )
        )

    return BuildOptionsCatalog(
        build_roles=[BuildRoleRead.model_validate(role) for role in list_build_roles(db)],
        categories=[BuildItemCategoryRead.model_validate(category) for category in categories],
        options=grouped,
        stat_definitions=stat_definitions_for_api(),
        research_upgrade_slot_effects=dict(RESEARCH_UPGRADE_SLOT_EFFECTS),
        limits=build_limits_for_api(),
    )
