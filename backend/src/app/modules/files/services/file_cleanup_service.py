from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.builds.models.build_file_attachment import BuildFileAttachment
from app.modules.files.models.file_asset import StoredFile
from app.modules.files.services.file_service import resolve_stored_file_path
from app.modules.forum.models.forum_post_attachment import ForumPostAttachment
from app.modules.guides.models.guide_attachment import GuideAttachment


def stage_unreferenced_files_for_deletion(
    db: Session, file_ids: set[int]
) -> set[Path]:
    """Stage file rows after their content associations were detached."""
    normalized_ids = {int(file_id) for file_id in file_ids if int(file_id) > 0}
    if not normalized_ids:
        return set()

    referenced_ids = set(
        db.scalars(
            select(BuildFileAttachment.file_id).where(
                BuildFileAttachment.file_id.in_(normalized_ids)
            )
        ).all()
    )
    referenced_ids.update(
        db.scalars(
            select(ForumPostAttachment.file_id).where(
                ForumPostAttachment.file_id.in_(normalized_ids)
            )
        ).all()
    )
    referenced_ids.update(
        db.scalars(
            select(GuideAttachment.file_id).where(
                GuideAttachment.file_id.in_(normalized_ids)
            )
        ).all()
    )
    orphaned = list(
        db.scalars(
            select(StoredFile).where(
                StoredFile.id.in_(normalized_ids - referenced_ids)
            )
        ).all()
    )
    paths = {
        path
        for stored_file in orphaned
        if (path := resolve_stored_file_path(stored_file)) is not None
    }
    for stored_file in orphaned:
        db.delete(stored_file)
    return paths


def remove_stored_file_paths(paths: set[Path]) -> None:
    for path in paths:
        path.unlink(missing_ok=True)
        try:
            path.parent.rmdir()
        except OSError:
            pass
