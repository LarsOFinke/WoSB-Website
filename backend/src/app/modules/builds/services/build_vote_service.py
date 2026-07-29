from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.builds.models.build import Build
from app.modules.builds.models.build_vote import BuildVote
from app.modules.builds.schemas.build_vote import BuildVoteState


def _state(db: Session, build_id: int, user_id: int) -> BuildVoteState | None:
    if db.get(Build, build_id) is None:
        return None
    count = int(
        db.scalar(select(func.count()).select_from(BuildVote).where(BuildVote.build_id == build_id))
        or 0
    )
    has_upvoted = db.scalar(
        select(BuildVote.id).where(
            BuildVote.build_id == build_id,
            BuildVote.user_id == user_id,
        )
    ) is not None
    return BuildVoteState(build_id=build_id, upvote_count=count, has_upvoted=has_upvoted)


def add_build_upvote(db: Session, build_id: int, user_id: int) -> BuildVoteState | None:
    if db.get(Build, build_id) is None:
        return None
    db.add(BuildVote(build_id=build_id, user_id=user_id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
    return _state(db, build_id, user_id)


def remove_build_upvote(db: Session, build_id: int, user_id: int) -> BuildVoteState | None:
    if db.get(Build, build_id) is None:
        return None
    db.execute(
        delete(BuildVote).where(
            BuildVote.build_id == build_id,
            BuildVote.user_id == user_id,
        )
    )
    db.commit()
    return _state(db, build_id, user_id)
