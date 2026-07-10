from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class BuildItemCategory(Base):
    __tablename__ = "build_item_categories"
    __table_args__ = (
        CheckConstraint("sort_order >= 0", name="ck_build_item_categories_sort_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    options: Mapped[list["BuildItemOption"]] = relationship(
        "BuildItemOption", back_populates="category", cascade="all, delete-orphan"
    )
