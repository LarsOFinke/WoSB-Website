from datetime import datetime
import re

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _parse_weapon_layout(layout: str | None) -> dict[str, int | float | None]:
    """Parse the compact ship weapon layout used by the seed catalog.

    Regular ships use ``front-broadside-rear`` where broadside is treated as
    the capacity for each side. Siege ships can additionally declare
    ``mortar <caliber>in x<count>``. The parser is deliberately permissive so
    old local seed strings continue to work.
    """

    result: dict[str, int | float | None] = {
        "front": 0,
        "broadside": 0,
        "rear": 0,
        "mortar": 0,
        "max_mortar_caliber_inches": None,
    }
    text = (layout or "").strip().lower()
    if not text:
        return result

    regular_match = re.search(r"(\d+)\s*-\s*(\d+)\s*-\s*(\d+)", text)
    if regular_match:
        result["front"] = int(regular_match.group(1))
        result["broadside"] = int(regular_match.group(2))
        result["rear"] = int(regular_match.group(3))

    mortar_match = re.search(r"mortar\s+(\d+(?:\.\d+)?)\s*in\s*x\s*(\d+)", text)
    if mortar_match:
        caliber = float(mortar_match.group(1))
        result["max_mortar_caliber_inches"] = int(caliber) if caliber.is_integer() else caliber
        result["mortar"] = int(mortar_match.group(2))

    return result


class Ship(Base):
    __tablename__ = "ships"
    __table_args__ = (
        CheckConstraint("rate >= 1 and rate <= 7", name="ck_ships_rate"),
        CheckConstraint("durability >= 0", name="ck_ships_durability"),
        CheckConstraint("speed_knots >= 0", name="ck_ships_speed_knots"),
        CheckConstraint("maneuverability >= 0", name="ck_ships_maneuverability"),
        CheckConstraint("armor >= 0", name="ck_ships_armor"),
        CheckConstraint("hold_capacity >= 0", name="ck_ships_hold_capacity"),
        CheckConstraint("crew_capacity >= 0", name="ck_ships_crew_capacity"),
        CheckConstraint("sailor_minimum >= 0", name="ck_ships_sailor_minimum"),
        CheckConstraint("displacement_tons >= 0", name="ck_ships_displacement_tons"),
        CheckConstraint("sail_slots >= 0", name="ck_ships_sail_slots"),
        CheckConstraint("upgrade_slots >= 0", name="ck_ships_upgrade_slots"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    rate: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    ship_type: Mapped[str] = mapped_column(String(80), nullable=False, default="Ship")
    durability: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    speed_knots: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    maneuverability: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    armor: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    hold_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    crew_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    sailor_minimum: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    weapon_layout: Mapped[str | None] = mapped_column(String(40), nullable=True)
    displacement_tons: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sail_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    upgrade_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    has_lantern: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    @property
    def weapon_layout_details(self) -> dict[str, int | float | None]:
        return _parse_weapon_layout(self.weapon_layout)

    @property
    def front_weapon_capacity(self) -> int:
        return int(self.weapon_layout_details["front"] or 0)

    @property
    def broadside_weapon_capacity(self) -> int:
        return int(self.weapon_layout_details["broadside"] or 0)

    @property
    def rear_weapon_capacity(self) -> int:
        return int(self.weapon_layout_details["rear"] or 0)

    @property
    def mortar_weapon_capacity(self) -> int:
        return int(self.weapon_layout_details["mortar"] or 0)

    @property
    def max_mortar_caliber_inches(self) -> int | float | None:
        return self.weapon_layout_details["max_mortar_caliber_inches"]

