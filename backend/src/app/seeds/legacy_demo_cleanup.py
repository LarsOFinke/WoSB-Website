from __future__ import annotations

from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.builds.models.build import Build
from app.modules.calendar.models.fleet_event import FleetEvent
from app.modules.files.models.file_asset import StoredFile
from app.modules.forum.models.forum import ForumThread
from app.modules.groups.models.group import Group
from app.modules.groups.models.group_member import GroupMember
from app.modules.guides.models.guide import Guide


# These identifiers belonged to the historic development/demo seed. Cleanup is
# deliberately conservative: records are removed only while their defining
# seed text still matches, so staff-edited content is not silently destroyed.
LEGACY_DEMO_BUILD_MARKERS = {
    "Victory Defensive Line": "Demo build for line/sustain play.",
    "Surprise Gunnery Scout": "Fast sample build for scouting",
    "Adventure Mortar Support": "Siege sample build",
}
LEGACY_DEMO_GUIDE_MARKERS = {
    "Port-Battle Line Basics": "A compact starter doctrine for line discipline",
    "Trade Convoy Checklist": "A practical checklist for safe fleet trade runs",
}
LEGACY_DEMO_THREAD_MARKERS = {
    "Practice feedback: line turns and repair cadence": "Last training showed better focus fire",
    "Weekly logistics: escort slots for trade convoy": "The trade fleet is collecting escort availability",
}
LEGACY_DEMO_GROUP_MARKERS = {
    "Evening PvE Farming Run": "Relaxed fleet announcement for resources",
    "Arena Practice Rotation": "Practice announcement for arena rotations",
}
LEGACY_DEMO_EVENT_MARKERS = {
    "Port Battle Briefing": "Fleet briefing, role assignment",
    "Gunnery Training": "Short practice block for arcs",
    "Fleet Farm Run": "Relaxed resource and XP farming round",
}
LEGACY_DEMO_FILE_PATHS = {"demo/line-battle.svg", "demo/trade-convoy.svg"}


def _matches(value: str | None, marker: str) -> bool:
    return bool(value and marker in value)


def cleanup_legacy_demo_content(db: Session) -> None:
    """Remove untouched historic sample activity from upgraded installations.

    Official progression templates and guides are seeded separately. This
    cleanup only retires the old development fixtures and leaves any edited or
    independently created records intact.
    """

    for group in db.scalars(select(Group).where(Group.title.in_(LEGACY_DEMO_GROUP_MARKERS))).all():
        if _matches(group.description, LEGACY_DEMO_GROUP_MARKERS[group.title]):
            db.delete(group)

    for event in db.scalars(select(FleetEvent).where(FleetEvent.title.in_(LEGACY_DEMO_EVENT_MARKERS))).all():
        if _matches(event.description, LEGACY_DEMO_EVENT_MARKERS[event.title]):
            db.delete(event)

    for thread in db.scalars(
        select(ForumThread).where(ForumThread.title.in_(LEGACY_DEMO_THREAD_MARKERS))
    ).unique().all():
        first_post = thread.posts[0] if thread.posts else None
        if first_post and _matches(first_post.body, LEGACY_DEMO_THREAD_MARKERS[thread.title]):
            db.delete(thread)

    for guide in db.scalars(select(Guide).where(Guide.title.in_(LEGACY_DEMO_GUIDE_MARKERS))).unique().all():
        if _matches(guide.summary, LEGACY_DEMO_GUIDE_MARKERS[guide.title]):
            db.delete(guide)

    db.flush()

    removable_builds: list[Build] = []
    for build in db.scalars(select(Build).where(Build.build_name.in_(LEGACY_DEMO_BUILD_MARKERS))).unique().all():
        if not build.is_official_template and _matches(build.details, LEGACY_DEMO_BUILD_MARKERS[build.build_name]):
            removable_builds.append(build)

    if removable_builds:
        removable_build_ids = [build.id for build in removable_builds]
        # A user may have selected a former sample build for an old group.
        # Preserve the group-member record while dropping only that optional
        # reference before deleting the fixture build.
        db.execute(
            update(GroupMember)
            .where(GroupMember.build_id.in_(removable_build_ids))
            .values(build_id=None)
        )
        for build in removable_builds:
            db.delete(build)

    db.flush()

    for stored_file in db.scalars(
        select(StoredFile).where(StoredFile.relative_path.in_(LEGACY_DEMO_FILE_PATHS))
    ).all():
        db.delete(stored_file)

    db.commit()

    upload_root = Path(settings.upload_dir).resolve()
    for relative_path in LEGACY_DEMO_FILE_PATHS:
        target = (upload_root / relative_path).resolve()
        if upload_root in target.parents and target.is_file():
            target.unlink(missing_ok=True)
