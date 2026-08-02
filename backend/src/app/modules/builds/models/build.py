from app.core.time import utc_now
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.modules.builds.models.build_constants import WEAPON_SLOT_TYPE_BY_ARC
from app.modules.builds.models.build_statistics import BuildStatisticsMixin
from app.modules.ships.models.ship import Ship

if TYPE_CHECKING:
    from app.modules.accounts.models.user import User
    from app.modules.builds.models.build_classification import BuildClassification
    from app.modules.builds.models.build_feature import BuildFeatureDefinition
    from app.modules.builds.models.build_slot import BuildSlot

class Build(BuildStatisticsMixin, Base):
    __tablename__ = "builds"
    __table_args__ = (
        CheckConstraint("sailors >= 0", name="ck_builds_sailors"),
        CheckConstraint("soldiers >= 0", name="ck_builds_soldiers"),
        CheckConstraint("musketeers >= 0", name="ck_builds_musketeers"),
        CheckConstraint("mercenaries >= 0", name="ck_builds_mercenaries"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    build_name: Mapped[str] = mapped_column(String(140), nullable=False, index=True)
    build_type: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("build_roles.slug", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        default="balanced",
        index=True,
    )
    ship_id: Mapped[int] = mapped_column(ForeignKey("ships.id"), nullable=False, index=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    is_official_template: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    research_upgrade_feature_id: Mapped[int | None] = mapped_column(
        ForeignKey("build_features.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    mortar_modification_installed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    sailors: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    soldiers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    musketeers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mercenaries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    printout_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    printout_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    printout_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    ship: Mapped[Ship] = relationship(lazy="joined")
    owner: Mapped["User | None"] = relationship("User", lazy="joined")
    research_upgrade_feature: Mapped["BuildFeatureDefinition | None"] = relationship(
        "BuildFeatureDefinition", lazy="selectin"
    )
    slots: Mapped[list["BuildSlot"]] = relationship(
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="BuildSlot.slot_type, BuildSlot.slot_index",
    )
    classifications: Mapped[list["BuildClassification"]] = relationship(
        cascade="all, delete-orphan",
        lazy="selectin",
        back_populates="build",
        order_by="BuildClassification.tag",
    )

    @property
    def classification_tags(self) -> list[str]:
        return [classification.tag for classification in self.classifications]

    @property
    def research_upgrade_slot_unlocked(self) -> bool:
        return self.research_upgrade_feature is not None

    @property
    def research_upgrade_slot_effects(self) -> dict[str, int | float]:
        if self.research_upgrade_feature is None:
            return {}
        return dict(self.research_upgrade_feature.stat_effects)

    @property
    def research_upgrade_slots(self) -> int:
        if self.research_upgrade_feature is None:
            return 0
        return max(0, int(self.research_upgrade_feature.upgrade_slots_granted or 0))

    @property
    def build_role_label(self) -> str:
        return getattr(self, "_build_role_label", self.build_type.replace("_", " ").title())

    @property
    def upvote_count(self) -> int:
        return max(0, int(getattr(self, "_upvote_count", 0)))

    @property
    def has_upvoted(self) -> bool:
        return bool(getattr(self, "_viewer_has_upvoted", False))

    def _first_option_name(self, slot_type: str) -> str | None:
        for slot in self.slots:
            if slot.slot_type == slot_type:
                return slot.option.name
        return None

    def _option_name_at(self, slot_type: str, index: int) -> str | None:
        for slot in self.slots:
            if slot.slot_type == slot_type and slot.slot_index == index:
                return slot.option.name
        return None

    def _upgrade_slot_at(self, index: int):
        for slot in self.slots:
            if slot.slot_type == "upgrade" and slot.slot_index == index:
                return slot
        return None

    def _inventory_slots(self, slot_type: str) -> list[dict[str, Any]]:
        return [
            {"item": slot.option.name, "quantity": slot.quantity or 1}
            for slot in self.slots
            if slot.slot_type == slot_type
        ]

    def _slot_quantity_total(self, slot_type: str) -> int:
        return sum(slot.quantity or 1 for slot in self.slots if slot.slot_type == slot_type)

    @property
    def sails(self) -> str | None:
        return self._first_option_name("sail")

    @property
    def lantern(self) -> str | None:
        return self._first_option_name("lantern")

    @property
    def upgrade_1(self) -> str | None:
        return self._option_name_at("upgrade", 1)

    @property
    def upgrade_2(self) -> str | None:
        return self._option_name_at("upgrade", 2)

    @property
    def upgrade_3(self) -> str | None:
        return self._option_name_at("upgrade", 3)

    @property
    def upgrade_4(self) -> str | None:
        return self._option_name_at("upgrade", 4)

    @property
    def upgrade_5(self) -> str | None:
        return self._option_name_at("upgrade", 5)

    @property
    def upgrade_6(self) -> str | None:
        return self._option_name_at("upgrade", 6)

    @property
    def upgrade_7(self) -> str | None:
        return self._option_name_at("upgrade", 7)

    @property
    def upgrade_8(self) -> str | None:
        return self._option_name_at("upgrade", 8)

    @property
    def front_weapon_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots(WEAPON_SLOT_TYPE_BY_ARC["front"])

    @property
    def rear_weapon_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots(WEAPON_SLOT_TYPE_BY_ARC["rear"])

    @property
    def port_weapon_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots(WEAPON_SLOT_TYPE_BY_ARC["port"])

    @property
    def starboard_weapon_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots(WEAPON_SLOT_TYPE_BY_ARC["starboard"])

    @property
    def mortar_weapon_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots(WEAPON_SLOT_TYPE_BY_ARC["mortar"])

    @property
    def special_weapon_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots(WEAPON_SLOT_TYPE_BY_ARC["special"])

    @property
    def special_crew_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots("special_crew")

    @property
    def ammunition_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots("ammunition")

    @property
    def consumable_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots("consumable")

    @property
    def hold_slots(self) -> list[dict[str, Any]]:
        return self._inventory_slots("hold")
