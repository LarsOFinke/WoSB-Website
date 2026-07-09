from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.seeds.ammunition import AMMUNITION_OPTIONS
from app.db.seeds.build_catalog_quality import (
    validate_ship_seed_data,
    validate_special_crew_seed_data,
    validate_upgrade_seed_data,
    validate_weapon_seed_data,
)
from app.db.seeds.categories import BUILD_ITEM_CATEGORIES
from app.db.seeds.consumables import CONSUMABLE_OPTIONS
from app.db.seeds.demo_builds import DEMO_BUILD_DATA
from app.db.seeds.demo_groups import DEMO_GROUP_DATA
from app.db.seeds.demo_fleet_events import demo_fleet_event_data
from app.db.seeds.demo_content import seed_demo_content
from app.db.seeds.fleets import FLEET_SEED_DATA
from app.db.seeds.hold_items import HOLD_OPTIONS
from app.db.seeds.lanterns import LANTERN_OPTIONS
from app.db.seeds.sails import SAIL_OPTIONS
from app.db.seeds.ships import SHIP_SEED_DATA
from app.db.seeds.special_crew import SPECIAL_CREW_OPTIONS
from app.db.seeds.upgrades import UPGRADE_OPTIONS
from app.db.seeds.users import seed_admin_user
from app.db.seeds.weapons import WEAPON_OPTIONS
from app.models import Build, BuildItemCategory, BuildItemEffect, BuildItemOption, Fleet, FleetEvent, Group, Ship, User
from app.schemas import BuildCreate
from app.services.build_service import BuildValidationError, create_build
from app.schemas.group import GroupCreate
from app.services.group_service import create_group

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
        self.seed_users()
        self.seed_fleets()
        self.seed_ships()
        self.seed_build_options()
        self.seed_demo_builds()
        self.seed_demo_groups()
        self.seed_demo_fleet_events()
        self.seed_demo_content()

    def seed_users(self) -> None:
        seed_admin_user(self.db)


    def seed_fleets(self) -> None:
        active_slugs = {row["slug"] for row in FLEET_SEED_DATA}
        for fleet_data in FLEET_SEED_DATA:
            existing = self.db.scalar(select(Fleet).where(Fleet.slug == fleet_data["slug"]))
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

    def seed_ships(self) -> None:
        validate_ship_seed_data(SHIP_SEED_DATA)
        for ship_data in SHIP_SEED_DATA:
            existing = self.db.scalar(select(Ship).where(Ship.name == ship_data["name"]))
            if existing is None:
                self.db.add(Ship(**ship_data))
                continue
            for field_name, value in ship_data.items():
                setattr(existing, field_name, value)
        self.db.commit()

    def seed_build_options(self) -> None:
        validate_upgrade_seed_data(UPGRADE_OPTIONS)
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
                    "allowed_slot_types": option_data.get("allowed_slot_types"),
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

        # Existing local DBs can contain old placeholder rows. Keep them for
        # historical builds, but hide them from dropdowns and validation.
        for option in self.db.scalars(select(BuildItemOption).join(BuildItemOption.category)).unique().all():
            pair = (option.category.key, option.name.casefold())
            if option.category.key in active_category_keys and pair not in active_pairs:
                option.is_active = False

        self.db.commit()


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

    def seed_demo_builds(self) -> None:
        existing_build = self.db.scalar(select(Build.id).limit(1))
        if existing_build is not None:
            return

        ships = {ship.name: ship for ship in self.db.scalars(select(Ship)).all()}
        demo_owner = self.db.scalar(select(User).where(User.role == "admin").order_by(User.id))
        owner_id = demo_owner.id if demo_owner else None
        for raw_build_data in DEMO_BUILD_DATA:
            build_data = dict(raw_build_data)
            ship_name = build_data.pop("ship_name")
            ship = ships.get(ship_name)
            if ship is None:
                continue
            try:
                create_build(self.db, BuildCreate(ship_id=ship.id, **build_data), owner_id=owner_id)
            except BuildValidationError as exc:
                raise RuntimeError(f"Demo build seed failed for {build_data['build_name']}: {exc}") from exc

    def seed_demo_groups(self) -> None:
        existing_group = self.db.scalar(select(Group.id).limit(1))
        if existing_group is not None:
            return

        demo_owner = self.db.scalar(select(User).where(User.role == "admin").order_by(User.id))
        if demo_owner is None:
            return

        for group_data in DEMO_GROUP_DATA:
            create_group(self.db, GroupCreate(**group_data), owner_id=demo_owner.id)


    def seed_demo_content(self) -> None:
        seed_demo_content(self.db)


    def seed_demo_fleet_events(self) -> None:
        existing_event = self.db.scalar(select(FleetEvent.id).limit(1))
        if existing_event is not None:
            return

        demo_owner = self.db.scalar(select(User).where(User.role == "admin").order_by(User.id))
        if demo_owner is None:
            return

        for event_data in demo_fleet_event_data():
            self.db.add(FleetEvent(owner_id=demo_owner.id, **event_data))
        self.db.commit()
