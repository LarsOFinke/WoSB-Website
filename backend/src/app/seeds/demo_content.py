from pathlib import Path
import shutil

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.accounts.models.user import User
from app.modules.builds.models.build import Build
from app.modules.files.models.file_asset import StoredFile
from app.modules.forum.models.forum import ForumThread
from app.modules.forum.models.forum_post import ForumPost
from app.modules.forum.models.forum_post_attachment import ForumPostAttachment
from app.modules.guides.models.guide import Guide
from app.modules.guides.models.guide_attachment import GuideAttachment
from app.modules.guides.models.guide_build_reference import GuideBuildReference

DEMO_FILES = [
    {
        "original_name": "line-battle.svg",
        "stored_name": "demo-line-battle.svg",
        "relative_path": "demo/line-battle.svg",
        "mime_type": "image/svg+xml",
        "usage_context": "demo",
    },
    {
        "original_name": "trade-convoy.svg",
        "stored_name": "demo-trade-convoy.svg",
        "relative_path": "demo/trade-convoy.svg",
        "mime_type": "image/svg+xml",
        "usage_context": "demo",
    },
]

DEMO_GUIDES = [
    {
        "title": "Port-Battle Line Basics",
        "category": "combat",
        "summary": "A compact starter doctrine for line discipline, focus calls and repair timing.",
        "body": """Use this as a lightweight doctrine before port-battle practice.

[[file:{file_id}|large]]

Recommended reference build:
[[build:{build_id}|card]]

1. Hold the assigned line unless the caller explicitly breaks formation.
2. Announce disabled sails, fire and low crew early.
3. Save hard turns for command calls or survival.
4. Repair on tempo: hull first, rigging when the line needs speed, crew only when boarding risk is real.

The goal is not perfect theorycrafting; it is shared vocabulary and fewer surprises during the first engagement.""",
        "file": "demo/line-battle.svg",
        "build": "Victory Defensive Line",
    },
    {
        "title": "Trade Convoy Checklist",
        "category": "economy",
        "summary": "A practical checklist for safe fleet trade runs and escort handoff.",
        "body": """Before departure, the convoy lead should publish route, cargo risk and escort needs.

[[file:{file_id}|medium]]

Scout escort build:
[[build:{build_id}|compact]]

Checklist:
- Confirm port of departure and fallback port.
- Split valuable cargo across multiple holds.
- Assign at least one scout ahead of the convoy.
- Keep voice comms short: sighting, heading, distance, ship count.
- Log losses and bottlenecks after the run so logistics can adapt the next route.""",
        "file": "demo/trade-convoy.svg",
        "build": "Surprise Gunnery Scout",
    },
]

DEMO_THREADS = [
    {
        "title": "Practice feedback: line turns and repair cadence",
        "category": "training",
        "body": """Last training showed better focus fire, but our turn timing still spreads the line.

[[file:{file_id}|medium]]

Please post short feedback: what call was clear, where did you lose the caller, and which repair timing felt too late?""",
        "file": "demo/line-battle.svg",
    },
    {
        "title": "Weekly logistics: escort slots for trade convoy",
        "category": "logistics",
        "body": """The trade fleet is collecting escort availability for this week.

[[file:{file_id}|small]]

Reply with your usual play window, ship rate and whether you prefer scout, screen or rear guard.""",
        "file": "demo/trade-convoy.svg",
    },
]


def _copy_demo_file(relative_path: str) -> int:
    source = Path(__file__).resolve().parent / "assets" / relative_path
    target = Path(settings.upload_dir) / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.exists() and not target.exists():
        shutil.copyfile(source, target)
    return target.stat().st_size if target.exists() else 0


def _stored_file(db: Session, owner: User, file_data: dict[str, str]) -> StoredFile:
    existing = db.scalar(select(StoredFile).where(StoredFile.relative_path == file_data["relative_path"]))
    size_bytes = _copy_demo_file(file_data["relative_path"])
    payload = {
        **file_data,
        "owner_id": owner.id,
        "size_bytes": size_bytes,
    }
    if existing is None:
        existing = StoredFile(**payload)
        db.add(existing)
        db.flush()
        return existing
    for field_name, value in payload.items():
        setattr(existing, field_name, value)
    return existing


def seed_demo_content(db: Session) -> None:
    owner = db.scalar(select(User).where(User.role == "admin").order_by(User.id))
    if owner is None:
        return

    files = {row["relative_path"]: _stored_file(db, owner, row) for row in DEMO_FILES}
    builds = {build.build_name: build for build in db.scalars(select(Build)).all()}

    for data in DEMO_GUIDES:
        existing = db.scalar(select(Guide).where(Guide.title == data["title"]))
        file = files[data["file"]]
        build = builds.get(data.get("build", ""))
        body = data["body"].format(file_id=file.id, build_id=build.id if build else 0)
        if existing is None:
            guide = Guide(
                title=data["title"],
                category=data["category"],
                summary=data["summary"],
                body=body,
                owner_id=owner.id,
            )
            guide.attachments.append(GuideAttachment(file_id=file.id, sort_order=0))
            if build is not None:
                guide.build_references.append(GuideBuildReference(build_id=build.id, sort_order=0))
            db.add(guide)
            continue
        existing.category = data["category"]
        existing.summary = data["summary"]
        existing.body = body
        existing.is_published = True
        if not any(attachment.file_id == file.id for attachment in existing.attachments):
            existing.attachments.append(GuideAttachment(file_id=file.id, sort_order=len(existing.attachments)))
        if build is not None and not any(reference.build_id == build.id for reference in existing.build_references):
            existing.build_references.append(GuideBuildReference(build_id=build.id, sort_order=len(existing.build_references)))

    for data in DEMO_THREADS:
        existing = db.scalar(select(ForumThread).where(ForumThread.title == data["title"]))
        file = files[data["file"]]
        build = builds.get(data.get("build", ""))
        body = data["body"].format(file_id=file.id, build_id=build.id if build else 0)
        if existing is not None:
            first_post = existing.posts[0] if existing.posts else None
            if first_post is not None:
                first_post.body = body
                if not any(attachment.file_id == file.id for attachment in first_post.attachments):
                    first_post.attachments.append(ForumPostAttachment(file_id=file.id, sort_order=len(first_post.attachments)))
            continue
        thread = ForumThread(title=data["title"], category=data["category"], owner_id=owner.id)
        first_post = ForumPost(body=body, author_id=owner.id)
        first_post.attachments.append(ForumPostAttachment(file_id=file.id, sort_order=0))
        thread.posts.append(first_post)
        db.add(thread)

    db.commit()
