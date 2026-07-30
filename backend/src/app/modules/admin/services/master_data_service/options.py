from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.admin.schemas.master_data import (
    MasterDataOptionCreate,
    MasterDataOptionRead,
    MasterDataOptionUpdate,
)
from app.modules.builds.models.build_item_category import BuildItemCategory
from app.modules.builds.models.build_item_effect import BuildItemEffect
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.builds.models.build_item_option_slot import BuildItemOptionSlotType
from app.bootstrap.catalog_sync import CUSTOM_MASTER_DATA_REVISION
from app.bootstrap.manager import SeedManager

from .common import MasterDataError, MasterDataUnitOfWork, TaxonomyRepository
from .mappers import MasterDataMapper


class OptionMasterDataService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self._uow = MasterDataUnitOfWork(db)
        self._taxonomy = TaxonomyRepository(db)

    @staticmethod
    def query():
        return select(BuildItemOption).options(
            selectinload(BuildItemOption.effects),
            selectinload(BuildItemOption.slot_type_links).selectinload(
                BuildItemOptionSlotType.slot_type
            ),
        )

    def list(
        self, *, category_key: str | None = None, search: str | None = None
    ) -> list[MasterDataOptionRead]:
        query = self.query().join(BuildItemOption.category)
        if category_key:
            query = query.where(BuildItemCategory.key == category_key)
        if search:
            query = query.where(func.lower(BuildItemOption.name).contains(search.strip().casefold()))
        rows = self.db.scalars(
            query.order_by(
                BuildItemCategory.sort_order,
                BuildItemOption.sort_order,
                func.lower(BuildItemOption.name),
            )
        ).unique().all()
        return [MasterDataMapper.option(row) for row in rows]

    def create(self, payload: MasterDataOptionCreate) -> MasterDataOptionRead:
        row = BuildItemOption(
            category_id=payload.category_id,
            name=payload.name,
            seed_revision=CUSTOM_MASTER_DATA_REVISION,
        )
        self.db.add(row)
        self._apply(row, payload)
        self._uow.commit("An option with this name already exists in the category.")
        return MasterDataMapper.option(self._reload(row.id))

    def update(self, option_id: int, payload: MasterDataOptionUpdate) -> MasterDataOptionRead:
        row = self._reload(option_id, required=False)
        if row is None:
            raise MasterDataError("Option not found.")
        self._apply(row, payload)
        if row.seed_key:
            row.is_seed_overridden = True
        self._uow.commit("An option with this name already exists in the category.")
        return MasterDataMapper.option(self._reload(option_id))

    def deactivate(self, option_id: int) -> None:
        row = self.db.get(BuildItemOption, option_id)
        if row is None:
            raise MasterDataError("Option not found.")
        row.is_active = False
        if row.seed_key:
            row.is_seed_overridden = True
        self.db.commit()

    def restore_seed(self, option_id: int) -> MasterDataOptionRead:
        row = self.db.get(BuildItemOption, option_id)
        if row is None or not row.seed_key:
            raise MasterDataError("This option has no seed default.")
        seed_key = row.seed_key
        row.is_seed_overridden = False
        row.seed_revision = None
        row.seed_checksum = None
        self.db.commit()
        SeedManager(self.db).seed_build_options()
        restored = self.db.scalar(self.query().where(BuildItemOption.seed_key == seed_key))
        if restored is None:
            raise MasterDataError("Seed default no longer exists.")
        return MasterDataMapper.option(restored)

    def _apply(
        self,
        row: BuildItemOption,
        payload: MasterDataOptionCreate | MasterDataOptionUpdate,
    ) -> None:
        category = self.db.get(BuildItemCategory, payload.category_id)
        if category is None:
            raise MasterDataError("Category not found.")
        weapon_classes, slot_types = self._taxonomy.maps()
        if payload.weapon_class and payload.weapon_class not in weapon_classes:
            raise MasterDataError("Unknown weapon class.")
        unknown_slots = set(payload.allowed_slot_types).difference(slot_types)
        if unknown_slots:
            raise MasterDataError(
                f"Unknown weapon slot types: {', '.join(sorted(unknown_slots))}"
            )

        if category.key == "weapon":
            expected_slots = {
                "cannon": {"weapon_port", "weapon_starboard"},
                "bow_stern": {"weapon_front", "weapon_rear"},
                "mortar": {"weapon_mortar"},
                "mortar_launcher": {"weapon_mortar"},
                "special_weapon": {
                    "weapon_front",
                    "weapon_rear",
                    "weapon_special",
                },
            }.get(payload.option_kind)
            if expected_slots is not None and set(payload.allowed_slot_types) != expected_slots:
                raise MasterDataError(
                    f"{payload.option_kind} weapons require exactly these slot types: "
                    f"{', '.join(sorted(expected_slots))}."
                )
            if payload.option_kind == "cannon" and not payload.weapon_class:
                raise MasterDataError(
                    "Broadside cannons require a Light, Medium or Heavy weapon class."
                )
            if payload.option_kind in {
                "bow_stern",
                "mortar",
                "mortar_launcher",
                "special_weapon",
            } and payload.weapon_class:
                raise MasterDataError(
                    "This weapon family is compatible by slot type and must not define a weapon class."
                )

        for field, value in payload.model_dump(
            exclude={"stat_effects", "allowed_slot_types", "weapon_class"}
        ).items():
            setattr(row, field, value)
        row.weapon_class_id = (
            weapon_classes[payload.weapon_class].id if payload.weapon_class else None
        )
        self._replace_effects(row, payload.stat_effects)
        self._replace_slots(row, payload.allowed_slot_types, slot_types)

    @staticmethod
    def _replace_effects(row: BuildItemOption, values: dict[str, float]) -> None:
        current = {effect.effect_key: effect for effect in row.effects}
        for key, value in values.items():
            effect = current.pop(key, None)
            if effect is None:
                row.effects.append(BuildItemEffect(effect_key=key, effect_value=float(value)))
            else:
                effect.effect_value = float(value)
        for effect in current.values():
            row.effects.remove(effect)

    @staticmethod
    def _replace_slots(row: BuildItemOption, codes: list[str], slot_types: dict) -> None:
        current = {link.slot_type.code: link for link in row.slot_type_links}
        for code in codes:
            if code not in current:
                row.slot_type_links.append(
                    BuildItemOptionSlotType(slot_type_id=slot_types[code].id)
                )
        for code, link in current.items():
            if code not in codes:
                row.slot_type_links.remove(link)

    def _reload(
        self, option_id: int, *, required: bool = True
    ) -> BuildItemOption | None:
        row = self.db.scalar(self.query().where(BuildItemOption.id == option_id))
        if required and row is None:
            raise MasterDataError(f"Build item option {option_id} disappeared during reload.")
        return row
