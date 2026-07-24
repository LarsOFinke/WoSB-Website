from sqlalchemy import select

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.modules.builds.models.build_item_category import BuildItemCategory
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.registry import register_all_models
from app.bootstrap.manager import SeedManager


def test_legacy_reinforced_ports_is_migrated_to_fortified_ports() -> None:
    register_all_models()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        category = db.scalar(select(BuildItemCategory).where(BuildItemCategory.key == "upgrade"))
        if category is None:
            category = BuildItemCategory(key="upgrade", label="Upgrades", sort_order=20, is_active=True)
            db.add(category)
            db.flush()

        legacy = db.scalar(
            select(BuildItemOption).where(
                BuildItemOption.category_id == category.id,
                BuildItemOption.name == "Reinforced Ports",
            )
        )
        if legacy is None:
            db.add(
                BuildItemOption(
                    category_id=category.id,
                    name="Reinforced Ports",
                    sort_order=999,
                    is_active=True,
                )
            )
            db.commit()

        manager = SeedManager(db)
        manager.seed_weapon_slot_types()
        manager.seed_build_options()

        legacy = db.scalar(
            select(BuildItemOption).where(
                BuildItemOption.category_id == category.id,
                BuildItemOption.name == "Reinforced Ports",
            )
        )
        current = db.scalar(
            select(BuildItemOption).where(
                BuildItemOption.category_id == category.id,
                BuildItemOption.name == "Fortified Ports",
            )
        )
        assert legacy is None
        assert current is not None
        assert current.is_active is True
        assert current.stat_effects == {"weapon_range": 10}
