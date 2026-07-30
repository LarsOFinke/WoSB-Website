from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.builds.models.build_feature import BuildFeatureDefinition
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.builds.services.build_role_service import BuildRoleError, require_build_role
from app.modules.builds.models.build_slot import BuildSlot
from app.modules.builds.schemas.build_create import BuildCreate
from app.modules.builds.services.build_limits import (
    CONSUMABLE_SLOT_LIMIT,
    SPECIAL_CREW_SLOT_LIMIT,
    regular_specialist_count,
)
from app.modules.builds.services.build_stat_service import (
    apply_percentage_effects,
    round_half_up,
)
from app.modules.builds.services.build_feature_service import get_research_upgrade_feature
from app.modules.builds.services.specialist_effect_service import resolve_specialist_effects
from app.modules.ships.models.ship import Ship

from .errors import BuildValidationError
from .options import BuildOptionCatalog, normalize_name
from .slots import BuildSlotFactory
from .upgrades import UpgradeAccessEvaluator
from .weapons import UniqueSlotValidator, WeaponLoadoutValidator


class BuildValidator:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._catalog = BuildOptionCatalog(db)
        self._weapons = WeaponLoadoutValidator()
        self._slots = BuildSlotFactory()

    def validate_and_prepare(
        self, build: BuildCreate
    ) -> tuple[Ship, list[BuildSlot], BuildFeatureDefinition | None]:
        try:
            require_build_role(self._db, build.build_type)
        except BuildRoleError as exc:
            raise BuildValidationError(str(exc)) from exc
        ship = self._db.get(Ship, build.ship_id)
        if ship is None or not ship.is_active:
            raise BuildValidationError("The selected ship does not exist.")
        if build.mortar_modification_installed and ship.mortar_modification is None:
            raise BuildValidationError(
                "The selected ship does not support the Mortar Modification."
            )

        research_feature = get_research_upgrade_feature(
            self._db, enabled=build.research_upgrade_slot_unlocked
        )
        if build.research_upgrade_slot_unlocked and research_feature is None:
            raise BuildValidationError("The upgrade add-on slot rule is unavailable.")

        option_map = self._catalog.load_for_build(build)
        upgrades = self._catalog.selected_upgrades(option_map, build)
        special_crew = self._catalog.selected_special_crew(option_map, build)
        self._validate_upgrade_slots(ship, build, upgrades, research_feature)
        self._validate_crew(
            ship, build, upgrades, special_crew, option_map, research_feature
        )
        self._weapons.validate(ship, build, option_map)
        self._validate_inventory(build)
        return ship, self._slots.create(build, option_map), research_feature

    @staticmethod
    def _validate_upgrade_slots(
        ship: Ship,
        build: BuildCreate,
        upgrades: dict[int, BuildItemOption],
        research_feature: BuildFeatureDefinition | None = None,
    ) -> None:
        access = UpgradeAccessEvaluator.evaluate(
            ship,
            upgrades,
            research_upgrade_slots=(
                int(research_feature.upgrade_slots_granted)
                if research_feature is not None
                else 0
            ),
        )
        rules = (
            (5, "slot_5_unlocked", "Upgrade slot 5 is locked. Enable the upgrade add-on slot or select an expansion upgrade in slots 1-4."),
            (6, "slot_6_available", "Upgrade slot 6 requires Structural Expansion or two one-slot sources."),
            (7, "slot_7_available", "Upgrade slot 7 requires Structural Expansion plus either the upgrade add-on slot or a ship-specific extra slot."),
            (8, "slot_8_available", "Upgrade slot 8 requires Structural Expansion, the upgrade add-on slot, and a ship-specific extra slot."),
        )
        for index, key, message in rules:
            if normalize_name(getattr(build, f"upgrade_{index}")) and not bool(access[key]):
                raise BuildValidationError(message)

    @staticmethod
    def _validate_crew(
        ship: Ship,
        build: BuildCreate,
        upgrades: dict[int, BuildItemOption],
        special_crew: list[tuple[BuildItemOption, int]],
        option_map: dict[tuple[str, str], BuildItemOption],
        research_feature: BuildFeatureDefinition | None = None,
    ) -> None:
        selected_equipment: list[BuildItemOption] = []
        if build.sails:
            selected_equipment.append(
                BuildOptionCatalog.require(option_map, build.sails, "sail", "Sail")
            )
        if build.lantern:
            selected_equipment.append(
                BuildOptionCatalog.require(option_map, build.lantern, "lantern", "Lantern")
            )
        effect_sets = [BuildOptionCatalog.effects(option, ship) for option in selected_equipment]
        effect_sets.extend(BuildOptionCatalog.effects(option, ship) for option in upgrades.values())
        effect_sets.extend(
            resolve_specialist_effects(
                [(BuildOptionCatalog.effects(option, ship), quantity)],
                sailors=build.sailors,
                soldiers=build.soldiers,
                musketeers=build.musketeers,
                mercenaries=build.mercenaries,
            )
            for option, quantity in special_crew
        )
        research_effects = (
            dict(research_feature.stat_effects) if research_feature is not None else {}
        )
        if research_effects:
            effect_sets.append(research_effects)
        mortar_modification_effects = ship.mortar_modification_effects(
            build.mortar_modification_installed
        )
        if mortar_modification_effects:
            effect_sets.append(mortar_modification_effects)

        totals: dict[str, int | float] = {}
        for effect_set in effect_sets:
            for key, value in effect_set.items():
                totals[key] = totals.get(key, 0) + value

        effective_capacity = max(
            0,
            round_half_up(
                apply_percentage_effects(
                    ship.crew_capacity,
                    "crew_capacity_pct",
                    effect_sets,
                    fallback_total=float(totals.get("crew_capacity_pct", 0) or 0),
                )
                + float(totals.get("crew_capacity", 0) or 0)
            ),
        )
        minimum_sailors = max(
            0, ship.sailor_minimum + int(totals.get("sailor_minimum", 0) or 0)
        )
        if build.sailors < minimum_sailors:
            raise BuildValidationError(
                f"Sailors ({build.sailors}) are below this build's required minimum ({minimum_sailors})."
            )
        crew_total = build.sailors + build.soldiers + build.musketeers + build.mercenaries
        if crew_total > effective_capacity:
            raise BuildValidationError(
                f"The crew distribution ({crew_total}) exceeds the effective ship capacity ({effective_capacity})."
            )

    @staticmethod
    def _validate_inventory(build: BuildCreate) -> None:
        for slots, label in (
            (build.special_crew_slots, "Special crew"),
            (build.ammunition_slots, "Ammunition"),
            (build.consumable_slots, "Consumables"),
            (build.hold_slots, "Hold"),
        ):
            UniqueSlotValidator.validate(slots, label)
        if regular_specialist_count([slot.item for slot in build.special_crew_slots]) > SPECIAL_CREW_SLOT_LIMIT:
            raise BuildValidationError(
                f"Special crew is limited to {SPECIAL_CREW_SLOT_LIMIT} regular specialists. Ginger uses an extra slot."
            )
        if len(build.consumable_slots) > CONSUMABLE_SLOT_LIMIT:
            raise BuildValidationError(
                f"Consumables are limited to {CONSUMABLE_SLOT_LIMIT} slots."
            )
