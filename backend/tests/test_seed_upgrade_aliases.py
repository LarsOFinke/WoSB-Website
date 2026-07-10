from sqlalchemy import select

from app.db.session import SessionLocal
from app.modules.builds.models.build_item_category import BuildItemCategory
from app.modules.builds.models.build_item_option import BuildItemOption
from app.seeds.manager import SeedManager


def test_legacy_fortified_ports_is_migrated_to_reinforced_ports() -> None:
    with SessionLocal() as db:
        category = db.scalar(select(BuildItemCategory).where(BuildItemCategory.key == "upgrade"))
        if category is None:
            category = BuildItemCategory(key="upgrade", label="Upgrades", sort_order=20, is_active=True)
            db.add(category)
            db.flush()

        legacy = db.scalar(
            select(BuildItemOption).where(
                BuildItemOption.category_id == category.id,
                BuildItemOption.name == "Fortified Ports",
            )
        )
        if legacy is None:
            db.add(
                BuildItemOption(
                    category_id=category.id,
                    name="Fortified Ports",
                    sort_order=999,
                    is_active=True,
                )
            )
            db.commit()

        SeedManager(db).seed_build_options()

        legacy = db.scalar(
            select(BuildItemOption).where(
                BuildItemOption.category_id == category.id,
                BuildItemOption.name == "Fortified Ports",
            )
        )
        current = db.scalar(
            select(BuildItemOption).where(
                BuildItemOption.category_id == category.id,
                BuildItemOption.name == "Reinforced Ports",
            )
        )
        assert legacy is None
        assert current is not None
        assert current.is_active is True
