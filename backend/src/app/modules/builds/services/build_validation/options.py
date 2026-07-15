from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.builds.models.build_item_category import BuildItemCategory
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.builds.schemas.build_create import BuildCreate
from app.modules.builds.services.build_limits import UPGRADE_SLOT_LIMIT
from app.modules.builds.services.ship_upgrade_effect_service import effective_upgrade_effects
from app.modules.ships.models.ship import Ship

from .constants import WEAPON_SLOT_TYPE_BY_FIELD
from .errors import BuildValidationError


def normalize_name(value: str | None) -> str | None:
    if not value:
        return None
    stripped = value.strip()
    return stripped or None


class BuildOptionCatalog:
    def __init__(self, db: Session) -> None:
        self._db = db

    def load_for_build(self, build: BuildCreate) -> dict[tuple[str, str], BuildItemOption]:
        return self.load(self.selected_item_names(build))

    def load(self, names: Iterable[str]) -> dict[tuple[str, str], BuildItemOption]:
        cleaned_names = {name.strip() for name in names if name and name.strip()}
        if not cleaned_names:
            return {}
        options = self._db.scalars(
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

    @staticmethod
    def require(
        option_map: dict[tuple[str, str], BuildItemOption],
        name: str,
        expected_category: str,
        label: str,
    ) -> BuildItemOption:
        option = option_map.get((expected_category, name.casefold()))
        if option is None:
            raise BuildValidationError(f"{label}: '{name}' is not a valid option.")
        return option

    @staticmethod
    def effects(option: BuildItemOption, ship: Ship | None = None) -> dict[str, int | float]:
        return effective_upgrade_effects(option, ship)

    @classmethod
    def selected_upgrades(
        cls,
        option_map: dict[tuple[str, str], BuildItemOption],
        build: BuildCreate,
    ) -> dict[int, BuildItemOption]:
        selected: dict[int, BuildItemOption] = {}
        selected_names: set[str] = set()
        for index in range(1, UPGRADE_SLOT_LIMIT + 1):
            name = normalize_name(getattr(build, f"upgrade_{index}"))
            if not name:
                continue
            normalized = name.casefold()
            if normalized in selected_names:
                raise BuildValidationError("Upgrades: each upgrade can only be selected once.")
            selected_names.add(normalized)
            selected[index] = cls.require(option_map, name, "upgrade", f"Upgrade {index}")
        return selected

    @classmethod
    def selected_special_crew(
        cls,
        option_map: dict[tuple[str, str], BuildItemOption],
        build: BuildCreate,
    ) -> list[tuple[BuildItemOption, int]]:
        return [
            (cls.require(option_map, slot.item, "special_crew", "Special crew"), 1)
            for slot in build.special_crew_slots
        ]

    @staticmethod
    def selected_item_names(build: BuildCreate) -> list[str]:
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
            normalized = normalize_name(value)
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
