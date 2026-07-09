from pathlib import Path
import shutil

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import (
    ForumPost,
    ForumPostAttachment,
    ForumThread,
    Guide,
    GuideAttachment,
    StoredFile,
    User,
)

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
        "body": """Use this as a lightweight doctrine before port-battle practice.\n\n1. Hold the assigned line unless the caller explicitly breaks formation.\n2. Announce disabled sails, fire and low crew early.\n3. Save hard turns for command calls or survival.\n4. Repair on tempo: hull first, rigging when the line needs speed, crew only when boarding risk is real.\n\nThe goal is not perfect theorycrafting; it is shared vocabulary and fewer surprises during the first engagement.""",
        "file": "demo/line-battle.svg",
    },
    {
        "title": "Trade Convoy Checklist",
        "category": "economy",
        "summary": "A practical checklist for safe fleet trade runs and escort handoff.",
        "body": """Before departure, the convoy lead should publish route, cargo risk and escort needs.\n\nChecklist:\n- Confirm port of departure and fallback port.\n- Split valuable cargo across multiple holds.\n- Assign at least one scout ahead of the convoy.\n- Keep voice comms short: sighting, heading, distance, ship count.\n- Log losses and bottlenecks after the run so logistics can adapt the next route.""",
        "file": "demo/trade-convoy.svg",
    },
]

DEMO_THREADS = [
    {
        "title": "Practice feedback: line turns and repair cadence",
        "category": "training",
        "body": "Last training showed better focus fire, but our turn timing still spreads the line. Please post short feedback: what call was clear, where did you lose the caller, and which repair timing felt too late?",
        "file": "demo/line-battle.svg",
    },
    {
        "title": "Weekly logistics: escort slots for trade convoy",
        "category": "logistics",
        "body": "The trade fleet is collecting escort availability for this week. Reply with your usual play window, ship rate and whether you prefer scout, screen or rear guard.",
        "file": "demo/trade-convoy.svg",
    },
]


def _copy_demo_file(relative_path: str) -> int:
    source = Path(__file__).resolve().parents[4] / "storage" / "uploads" / relative_path
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

    for data in DEMO_GUIDES:
        existing = db.scalar(select(Guide).where(Guide.title == data["title"]))
        file = files[data["file"]]
        if existing is None:
            guide = Guide(
                title=data["title"],
                category=data["category"],
                summary=data["summary"],
                body=data["body"],
                owner_id=owner.id,
            )
            guide.attachments.append(GuideAttachment(file_id=file.id, sort_order=0))
            db.add(guide)
            continue
        existing.category = data["category"]
        existing.summary = data["summary"]
        existing.body = data["body"]
        existing.is_published = True
        if not any(attachment.file_id == file.id for attachment in existing.attachments):
            existing.attachments.append(GuideAttachment(file_id=file.id, sort_order=len(existing.attachments)))

    for data in DEMO_THREADS:
        existing = db.scalar(select(ForumThread).where(ForumThread.title == data["title"]))
        file = files[data["file"]]
        if existing is not None:
            continue
        thread = ForumThread(title=data["title"], category=data["category"], owner_id=owner.id)
        first_post = ForumPost(body=data["body"], author_id=owner.id)
        first_post.attachments.append(ForumPostAttachment(file_id=file.id, sort_order=0))
        thread.posts.append(first_post)
        db.add(thread)

    db.commit()
