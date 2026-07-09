from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


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
