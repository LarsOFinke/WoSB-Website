from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.seeds.ammunition import AMMUNITION_OPTIONS
from app.seeds.build_catalog_quality import (
    validate_build_option_catalog,
    validate_lantern_seed_data,
    validate_ship_seed_data,
    validate_special_crew_seed_data,
    validate_upgrade_seed_data,
    validate_weapon_seed_data,
)
from app.seeds.categories import BUILD_ITEM_CATEGORIES
from app.seeds.consumables import CONSUMABLE_OPTIONS
from app.seeds.fleets import FLEET_SEED_DATA, LEGACY_FLEET_SLUGS
from app.seeds.hold_items import HOLD_OPTIONS
from app.seeds.lanterns import LANTERN_OPTIONS
from app.seeds.legacy_demo_cleanup import cleanup_legacy_demo_content
from app.seeds.newcomer_guide import seed_newcomer_guide
from app.seeds.starter_content import seed_starter_content
from app.seeds.weapon_mounts import WEAPON_CLASS_DATA, WEAPON_SLOT_TYPE_DATA, parse_weapon_layout
from app.seeds.sails import SAIL_OPTIONS
from app.seeds.ships import SHIP_SEED_DATA
from app.seeds.special_crew import SPECIAL_CREW_OPTIONS
from app.seeds.upgrades import LEGACY_UPGRADE_NAME_ALIASES, UPGRADE_OPTIONS
from app.seeds.users import seed_admin_user
from app.seeds.weapons import WEAPON_OPTIONS
from app.modules.builds.models.build_item_category import BuildItemCategory
from app.modules.builds.models.build_item_effect import BuildItemEffect
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.builds.models.build_item_option_slot import BuildItemOptionSlotType
from app.modules.builds.models.build_slot import BuildSlot
from app.modules.fleet.models.fleet import Fleet
from app.modules.ships.models.ship import Ship
from app.modules.ships.models.weapon_mount import ShipWeaponMount, WeaponClassDefinition, WeaponSlotType
from app.modules.permissions.services.role_service import ensure_role_catalog

BUILD_OPTION_SEED_GROUPS = (
    SAIL_OPTIONS,
    UPGRADE_OPTIONS,
    LANTERN_OPTIONS,
    AMMUNITION_OPTIONS,
    CONSUMABLE_OPTIONS,
    HOLD_OPTIONS,
    WEAPON_OPTIONS,
    SPECIAL_CREW_OPTIONS,
)


def _alphabetical_options(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(rows, key=lambda row: str(row["name"]).casefold())


class SeedManager:
    def __init__(self, db: Session) -> None:
        self.db = db

    def run(self) -> None:
        self.seed_role_catalog()
        self.seed_users()
        self.seed_fleets()
        self.seed_weapon_slot_types()
        self.seed_ships()
        self.seed_build_options()
        self.cleanup_legacy_demo_content()
        self.seed_starter_content()
        self.seed_newcomer_guide()

    def seed_role_catalog(self) -> None:
        ensure_role_catalog(self.db)
        self.db.commit()

    def seed_users(self) -> None:
        seed_admin_user(self.db)


    def seed_fleets(self) -> None:
        active_slugs = {row["slug"] for row in FLEET_SEED_DATA}
        for fleet_data in FLEET_SEED_DATA:
            existing = self.db.scalar(select(Fleet).where(Fleet.slug == fleet_data["slug"]))
            if existing is None:
                existing = self.db.scalar(select(Fleet).where(Fleet.slug.in_(LEGACY_FLEET_SLUGS)))
            payload = {**fleet_data, "is_active": fleet_data.get("is_active", True)}
            if existing is None:
                self.db.add(Fleet(**payload))
                continue
            for field_name, value in payload.items():
                setattr(existing, field_name, value)
        for fleet in self.db.scalars(select(Fleet)).all():
            if fleet.slug not in active_slugs and fleet.sort_order >= 10:
                fleet.is_active = False
        self.db.commit()

    def seed_weapon_slot_types(self) -> None:
        for row in WEAPON_CLASS_DATA:
            existing = self.db.scalar(select(WeaponClassDefinition).where(WeaponClassDefinition.code == row["code"]))
            if existing is None:
                self.db.add(WeaponClassDefinition(**row))
            else:
                for field_name, value in row.items():
                    setattr(existing, field_name, value)
        for row in WEAPON_SLOT_TYPE_DATA:
            existing = self.db.scalar(select(WeaponSlotType).where(WeaponSlotType.code == row["code"]))
            if existing is None:
                self.db.add(WeaponSlotType(**row))
            else:
                for field_name, value in row.items():
                    setattr(existing, field_name, value)
        self.db.commit()

    def seed_ships(self) -> None:
        validate_ship_seed_data(SHIP_SEED_DATA)
        slot_types = {row.code: row for row in self.db.scalars(select(WeaponSlotType)).all()}
        weapon_classes = {row.code: row for row in self.db.scalars(select(WeaponClassDefinition)).all()}
        for ship_data in SHIP_SEED_DATA:
            payload = dict(ship_data)
            layout = str(payload.pop("weapon_layout", ""))
            max_weapon_class = payload.pop("max_weapon_class", None)
            existing = self.db.scalar(select(Ship).where(Ship.name == payload["name"]))
            if existing is None:
                existing = Ship(**payload)
                self.db.add(existing)
                self.db.flush()
            else:
                for field_name, value in payload.items():
                    setattr(existing, field_name, value)
            mounts = {mount.slot_type.code: mount for mount in existing.weapon_mounts}
            active_codes: set[str] = set()
            for mount_data in parse_weapon_layout(
                layout,
                rate=int(payload["rate"]),
                max_weapon_class=str(max_weapon_class) if max_weapon_class else None,
            ):
                code = str(mount_data.pop("slot_type"))
                class_code = mount_data.pop("max_weapon_class", None)
                active_codes.add(code)
                mount = mounts.get(code)
                values = {
                    **mount_data,
                    "slot_type_id": slot_types[code].id,
                    "max_weapon_class_id": weapon_classes[str(class_code)].id if class_code else None,
                }
                if mount is None:
                    existing.weapon_mounts.append(ShipWeaponMount(**values))
                else:
                    for field_name, value in values.items():
                        setattr(mount, field_name, value)
            for code, mount in mounts.items():
                if code not in active_codes:
                    existing.weapon_mounts.remove(mount)
        self.db.commit()

    def seed_build_options(self) -> None:
        if not self.db.scalar(select(WeaponSlotType.id).limit(1)):
            self.seed_weapon_slot_types()
        validate_build_option_catalog(BUILD_ITEM_CATEGORIES, BUILD_OPTION_SEED_GROUPS)
        validate_upgrade_seed_data(UPGRADE_OPTIONS)
        validate_lantern_seed_data(LANTERN_OPTIONS)
        validate_weapon_seed_data(WEAPON_OPTIONS)
        validate_special_crew_seed_data(SPECIAL_CREW_OPTIONS)
        categories: dict[str, BuildItemCategory] = {}
        active_category_keys = {category["key"] for category in BUILD_ITEM_CATEGORIES}

        for category_data in BUILD_ITEM_CATEGORIES:
            existing = self.db.scalar(select(BuildItemCategory).where(BuildItemCategory.key == category_data["key"]))
            payload = {**category_data, "is_active": category_data.get("is_active", True)}
            if existing is None:
                existing = BuildItemCategory(**payload)
                self.db.add(existing)
                self.db.flush()
            else:
                for field_name, value in payload.items():
                    setattr(existing, field_name, value)
            categories[existing.key] = existing

        # Deactivate categories that used to exist in the DB but are no longer managed.
        for category in self.db.scalars(select(BuildItemCategory)).all():
            if category.key not in active_category_keys:
                category.is_active = False

        self._migrate_legacy_upgrade_names(categories["upgrade"])
        weapon_classes = {row.code: row for row in self.db.scalars(select(WeaponClassDefinition)).all()}

        active_pairs: set[tuple[str, str]] = set()
        for option_group in BUILD_OPTION_SEED_GROUPS:
            for sort_order, option_data in enumerate(_alphabetical_options(list(option_group)), start=10):
                category_key = str(option_data["category"])
                category = categories[category_key]
                option_name = str(option_data["name"]).strip()
                active_pairs.add((category_key, option_name.casefold()))

                lookup = select(BuildItemOption).where(
                    BuildItemOption.category_id == category.id,
                    BuildItemOption.name == option_name,
                )
                existing = self.db.scalar(lookup)
                raw_effects = option_data.get("stat_effects")
                payload = {
                    "category_id": category.id,
                    "name": option_name,
                    "source": option_data.get("source"),
                    "notes": option_data.get("notes"),
                    "option_kind": option_data.get("option_kind"),
                    "weapon_class_id": (
                        weapon_classes[str(option_data["weapon_class"])].id
                        if option_data.get("weapon_class")
                        else None
                    ),
                    "weapon_caliber_inches": option_data.get("weapon_caliber_inches"),
                    "sort_order": sort_order * 10,
                    "is_active": option_data.get("is_active", True),
                }
                if existing is None:
                    existing = BuildItemOption(**payload)
                    self.db.add(existing)
                    self.db.flush()
                else:
                    for field_name, value in payload.items():
                        setattr(existing, field_name, value)
                self._sync_option_effects(existing, raw_effects if isinstance(raw_effects, dict) else {})
                self._sync_option_slot_types(existing, str(option_data.get("allowed_slot_types") or ""))

        # Existing local DBs can contain old placeholder rows. Keep them for
        # historical builds, but hide them from dropdowns and validation.
        for option in self.db.scalars(select(BuildItemOption).join(BuildItemOption.category)).unique().all():
            pair = (option.category.key, option.name.casefold())
            if option.category.key in active_category_keys and pair not in active_pairs:
                option.is_active = False

        self.db.commit()


    def _sync_option_slot_types(self, option: BuildItemOption, raw_codes: str) -> None:
        codes = {code.strip() for code in raw_codes.split(",") if code.strip()}
        slot_types = {row.code: row for row in self.db.scalars(select(WeaponSlotType)).all()}
        unknown = codes.difference(slot_types)
        if unknown:
            raise ValueError(f"Unknown weapon slot types for {option.name}: {sorted(unknown)}")
        current = {link.slot_type.code: link for link in option.slot_type_links}
        for code in codes:
            if code not in current:
                option.slot_type_links.append(BuildItemOptionSlotType(slot_type_id=slot_types[code].id))
        for code, link in list(current.items()):
            if code not in codes:
                option.slot_type_links.remove(link)


    def cleanup_legacy_demo_content(self) -> None:
        cleanup_legacy_demo_content(self.db)

    def seed_starter_content(self) -> None:
        seed_starter_content(self.db)

    def _migrate_legacy_upgrade_names(self, category: BuildItemCategory) -> None:
        """Preserve saved builds while moving renamed upgrade options forward."""

        for legacy_name, current_name in LEGACY_UPGRADE_NAME_ALIASES.items():
            legacy = self.db.scalar(
                select(BuildItemOption).where(
                    BuildItemOption.category_id == category.id,
                    BuildItemOption.name == legacy_name,
                )
            )
            if legacy is None:
                continue

            current = self.db.scalar(
                select(BuildItemOption).where(
                    BuildItemOption.category_id == category.id,
                    BuildItemOption.name == current_name,
                )
            )
            if current is None:
                legacy.name = current_name
                legacy.is_active = True
                self.db.flush()
                continue

            self.db.execute(
                update(BuildSlot)
                .where(BuildSlot.option_id == legacy.id)
                .values(option_id=current.id)
            )
            self.db.delete(legacy)
            self.db.flush()


    def _sync_option_effects(self, option: BuildItemOption, effects: dict[str, object]) -> None:
        current = {effect.effect_key: effect for effect in option.effects}
        active_keys: set[str] = set()
        for key, value in sorted(effects.items()):
            if not isinstance(key, str) or not isinstance(value, (int, float)):
                continue
            active_keys.add(key)
            if key in current:
                current[key].effect_value = float(value)
            else:
                option.effects.append(BuildItemEffect(effect_key=key, effect_value=float(value)))
        for key, effect in list(current.items()):
            if key not in active_keys:
                option.effects.remove(effect)

    def seed_newcomer_guide(self) -> None:
        seed_newcomer_guide(self.db)
