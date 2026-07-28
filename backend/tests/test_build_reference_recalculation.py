from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.bootstrap.manager import SeedManager
from app.db.base import Base
from app.modules.builds.models.build_item_effect import BuildItemEffect
from app.modules.builds.models.build_item_option import BuildItemOption
from app.modules.builds.schemas.build_create import BuildCreate
from app.modules.builds.services.build_service import create_build, get_build
from app.modules.registry import register_all_models
from app.modules.ships.models.ship import Ship


def test_saved_build_recalculates_from_current_ship_and_option_references() -> None:
    """A persisted build stores inputs/references, never a calculated result snapshot."""

    register_all_models()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine, expire_on_commit=False) as db:
        manager = SeedManager(db)
        manager.seed_weapon_slot_types()
        manager.seed_ships()
        manager.seed_build_options()

        ship = db.scalar(select(Ship).where(Ship.name == "De Zeven Provincien"))
        assert ship is not None
        build = create_build(
            db,
            BuildCreate(
                build_name="Reference-based calculation",
                ship_id=ship.id,
                sails="Raiding Sails",
                sailors=ship.sailor_minimum,
            ),
        )
        build_id = build.id
        ship_id = ship.id
        assert build.ship_stats["effective_stats"]["speed_knots"] == 14.7

    # Simulate corrected master data arriving later through a seed/admin update.
    with Session(engine) as db:
        ship = db.scalar(select(Ship).where(Ship.name == "De Zeven Provincien"))
        sails = db.scalar(select(BuildItemOption).where(BuildItemOption.name == "Raiding Sails"))
        assert ship is not None and sails is not None
        speed_effect = db.scalar(
            select(BuildItemEffect).where(
                BuildItemEffect.option_id == sails.id,
                BuildItemEffect.effect_key == "speed_knots",
            )
        )
        assert speed_effect is not None
        ship.speed_knots = 11.0
        speed_effect.effect_value = 4.3
        db.commit()

    # The unchanged historical build must immediately reflect current references.
    with Session(engine, expire_on_commit=False) as db:
        recalculated = get_build(db, build_id)
        assert recalculated is not None
        assert recalculated.ship_id == ship_id
        assert recalculated.sails == "Raiding Sails"
        assert recalculated.ship_stats["base_stats"]["speed_knots"] == 11.0
        assert recalculated.ship_stats["sail_effects"]["speed_knots"] == 4.3
        assert recalculated.ship_stats["effective_stats"]["speed_knots"] == 15.3
