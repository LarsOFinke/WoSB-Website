import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.modules.fleet.models.fleet import Fleet
from app.modules.registry import register_all_models
from app.bootstrap.manager import SeedManager


@pytest.mark.parametrize(
    ("legacy_name", "legacy_slug"),
    [
        ("Royal Blackwater Vanguards", "royal-blackwater-vanguards"),
        ("Blackwater Mercenaries", "blackwater-mercenaries"),
    ],
)
def test_legacy_fleet_is_renamed_without_replacing_its_identity(tmp_path, legacy_name, legacy_slug):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy-brand.db'}")
    register_all_models()
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        legacy = Fleet(
            name=legacy_name,
            slug=legacy_slug,
            focus="mixed",
            description="legacy",
            standing_orders="legacy",
            sort_order=10,
            is_active=True,
        )
        db.add(legacy)
        db.commit()
        legacy_id = legacy.id

        SeedManager(db).seed_fleets()

        fleet = db.scalar(select(Fleet).where(Fleet.slug == "royal-blackwater-fleet"))
        assert fleet is not None
        assert fleet.id == legacy_id
        assert fleet.name == "Royal Blackwater Fleet"
        assert db.scalar(select(Fleet).where(Fleet.slug == legacy_slug)) is None
