from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import BuildOption


class BuildOptionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, *, category: str | None = None) -> list[BuildOption]:
        stmt = select(BuildOption)
        if category:
            stmt = stmt.where(BuildOption.category == category)
        stmt = stmt.order_by(BuildOption.category.asc(), BuildOption.name.asc())
        return list(self.db.scalars(stmt).all())

    def create_many(self, options: list[BuildOption]) -> None:
        self.db.add_all(options)
        self.db.flush()
