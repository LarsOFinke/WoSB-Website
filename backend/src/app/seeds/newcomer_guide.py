from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounts.models.user import User
from app.modules.builds.models.build import Build
from app.modules.guides.models.guide import Guide
from app.modules.onboarding.models.newcomer_guide import (
    NewcomerGuideBlock,
    NewcomerGuidePage,
    NewcomerGuideResource,
)


def seed_newcomer_guide(db: Session) -> None:
    if db.get(NewcomerGuidePage, 1) is not None:
        return

    admin = db.scalar(select(User).where(User.role == "admin").order_by(User.id))
    guides = {guide.title: guide for guide in db.scalars(select(Guide).where(Guide.is_published.is_(True))).all()}
    builds = {build.build_name: build for build in db.scalars(select(Build)).all()}

    page = NewcomerGuidePage(
        id=1,
        title="New Captain Guide",
        intro=(
            "A curated route from your first login to confident fleet participation. "
            "Work through the sections in order, ask questions early and check the calendar before joining operations."
        ),
        updated_by_id=admin.id if admin else None,
    )
    page.blocks.append(
        NewcomerGuideBlock(
            block_type="text",
            title="Welcome aboard",
            body=(
                "Start with the basics, copy a proven build instead of improvising, and use the forum whenever a guide leaves a question open. "
                "Discord voice is optional for everyday activity and mandatory for port battles and other competitive operations."
            ),
            sort_order=10,
        )
    )
    route = NewcomerGuideBlock(
        block_type="resources",
        title="Your first route",
        body="Open these resources in order and return here whenever you need orientation.",
        sort_order=20,
    )
    resources: list[NewcomerGuideResource] = []
    line_guide = guides.get("Port-Battle Line Basics")
    convoy_guide = guides.get("Trade Convoy Checklist")
    victory_build = builds.get("Victory Defensive Line")
    scout_build = builds.get("Surprise Gunnery Scout")
    if line_guide:
        resources.append(NewcomerGuideResource(resource_type="guide", resource_id=line_guide.id, sort_order=10))
    if victory_build:
        resources.append(NewcomerGuideResource(resource_type="build", resource_id=victory_build.id, sort_order=20))
    if convoy_guide:
        resources.append(NewcomerGuideResource(resource_type="guide", resource_id=convoy_guide.id, sort_order=30))
    if scout_build:
        resources.append(NewcomerGuideResource(resource_type="build", resource_id=scout_build.id, sort_order=40))
    resources.extend(
        [
            NewcomerGuideResource(
                resource_type="internal",
                label="Ask the fleet",
                description="Use the forum for Q&A that should remain searchable for the next newcomer.",
                url="/forum",
                sort_order=50,
            ),
            NewcomerGuideResource(
                resource_type="internal",
                label="Check scheduled operations",
                description="Review the calendar and prepare your ship before the event starts.",
                url="/calendar",
                sort_order=60,
            ),
        ]
    )
    route.resources.extend(resources)
    page.blocks.append(route)
    page.blocks.append(
        NewcomerGuideBlock(
            block_type="text",
            title="Competitive operations",
            body=(
                "Main fleet activity is usually between 12:00 and 02:00 CET, with port-battle focus from 18:00 to 23:00 CET. "
                "Join Discord voice before competitive operations, follow the caller and arrive with the announced build and supplies."
            ),
            sort_order=30,
        )
    )
    db.add(page)
    db.commit()
