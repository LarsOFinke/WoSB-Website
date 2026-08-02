from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.builds.models.build import Build
from app.modules.builds.models.build_file_attachment import BuildFileAttachment
from app.modules.builds.services.build_printout_service import printout_path
from app.modules.files.services.file_cleanup_service import (
    remove_stored_file_paths,
    stage_unreferenced_files_for_deletion,
)


def delete_build_and_files(db: Session, build: Build) -> None:
    attachments = list(
        db.scalars(
            select(BuildFileAttachment).where(BuildFileAttachment.build_id == build.id)
        ).all()
    )
    file_ids = {attachment.file_id for attachment in attachments}
    for attachment in attachments:
        db.delete(attachment)
    db.flush()
    paths = stage_unreferenced_files_for_deletion(db, file_ids)
    printout = printout_path(build.id)
    db.delete(build)
    db.commit()

    remove_stored_file_paths(paths | {printout})
