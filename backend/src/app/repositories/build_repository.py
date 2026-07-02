from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Build


_BUILD_LOAD_OPTIONS = (selectinload(Build.ship), selectinload(Build.author))


class BuildRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, build_id: int) -> Build | None:
        stmt = select(Build).where(Build.id == build_id).options(*_BUILD_LOAD_OPTIONS)
        return self.db.scalars(stmt).first()

    def list(self, *, limit: int = 100) -> list[Build]:
        stmt = select(Build).options(*_BUILD_LOAD_OPTIONS).order_by(Build.created_at.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())

    def create(self, build: Build) -> Build:
        self.db.add(build)
        self.db.flush()
        self.db.refresh(build)
        return build
