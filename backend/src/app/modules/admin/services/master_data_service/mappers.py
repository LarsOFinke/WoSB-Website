from __future__ import annotations

from app.modules.admin.schemas.master_data import (
    MasterDataCategoryRead,
    MasterDataOptionRead,
    MasterDataShipMortarModification,
    MasterDataShipMount,
    MasterDataShipRead,
    MasterDataShipUpgradeOverrideRead,
)
from app.modules.builds.models.build_item_category import BuildItemCategory
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.builds.services.ship_upgrade_effect_service import effective_upgrade_effects
from app.modules.ships.models.ship import Ship

from .common import seed_status


class MasterDataMapper:
    @staticmethod
    def category(row: BuildItemCategory) -> MasterDataCategoryRead:
        return MasterDataCategoryRead(
            id=row.id,
            key=row.key,
            label=row.label,
            sort_order=row.sort_order,
            is_active=row.is_active,
            seed_key=row.seed_key,
            seed_revision=row.seed_revision,
            is_seed_overridden=row.is_seed_overridden,
            seed_status=seed_status(row),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def option(row: BuildItemOption) -> MasterDataOptionRead:
        return MasterDataOptionRead(
            id=row.id,
            category_id=row.category_id,
            category_key=row.category.key,
            category_label=row.category.label,
            name=row.name,
            source=row.source,
            notes=row.notes,
            image_url=row.image_url,
            option_kind=row.option_kind,
            weapon_class=row.weapon_class_code,
            weapon_caliber_inches=row.weapon_caliber_inches,
            stat_effects=row.stat_effects,
            allowed_slot_types=row.allowed_slots,
            sort_order=row.sort_order,
            is_active=row.is_active,
            seed_key=row.seed_key,
            seed_revision=row.seed_revision,
            is_seed_overridden=row.is_seed_overridden,
            seed_status=seed_status(row),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def ship(row: Ship) -> MasterDataShipRead:
        mounts = [
            MasterDataShipMount(
                slot_type=mount.slot_type.code,
                capacity=mount.capacity,
                special_weapon_capacity=mount.special_weapon_capacity,
                max_weapon_class=(mount.max_weapon_class.code if mount.max_weapon_class else None),
                max_caliber_inches=mount.max_caliber_inches,
            )
            for mount in sorted(row.weapon_mounts, key=lambda item: item.slot_type.sort_order)
        ]
        overrides: list[MasterDataShipUpgradeOverrideRead] = []
        for option_id in sorted({item.option_id for item in row.upgrade_effect_overrides}):
            rows = [item for item in row.upgrade_effect_overrides if item.option_id == option_id]
            option = rows[0].option
            overrides.append(
                MasterDataShipUpgradeOverrideRead(
                    option_id=option.id,
                    option_name=option.name,
                    stat_effects={item.effect_key: item.normalized_value for item in rows},
                    base_stat_effects=option.stat_effects,
                    effective_stat_effects=effective_upgrade_effects(option, row),
                )
            )
        return MasterDataShipRead(
            id=row.id,
            name=row.name,
            rate=row.rate,
            ship_type=row.ship_type,
            durability=row.durability,
            speed_min_knots=row.speed_min_knots,
            speed_knots=row.speed_knots,
            maneuverability=row.maneuverability,
            armor=row.armor,
            hold_capacity=row.hold_capacity,
            crew_capacity=row.crew_capacity,
            sailor_minimum=row.sailor_minimum,
            displacement_tons=row.displacement_tons,
            source=row.source,
            image_url=row.image_url,
            sail_slots=row.sail_slots,
            upgrade_slots=row.upgrade_slots,
            has_lantern=row.has_lantern,
            is_active=row.is_active,
            weapon_mounts=mounts,
            mortar_modification=(
                MasterDataShipMortarModification.model_validate(
                    row.mortar_modification,
                    from_attributes=True,
                )
                if row.mortar_modification is not None
                else None
            ),
            upgrade_effect_overrides=overrides,
            weapon_layout=row.weapon_layout,
            seed_key=row.seed_key,
            seed_revision=row.seed_revision,
            is_seed_overridden=row.is_seed_overridden,
            seed_status=seed_status(row),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
