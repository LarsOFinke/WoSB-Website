from __future__ import annotations

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
from app.modules.permissions.models.role import SiteRoleDefinition


LEGACY_DEFAULT_BLOCK_TITLES = {
    "Welcome aboard",
    "Your first route",
    "Competitive operations",
}
LEGACY_DEFAULT_INTRO = (
    "A curated route from your first login to confident fleet participation. "
    "Work through the sections in order, ask questions early and check the calendar before joining operations."
)
PROGRESSION_INTRO = (
    "A practical progression route from the first login through trade, early frigates, mobility, "
    "Poltava training and eventual fleet-line readiness. Economy values are targets, not guarantees."
)


PROGRESSION_BLOCKS = (
    {
        "title": "Phase 1 · First five hours",
        "body": "Learn controls, complete the first reliable activities and preserve enough liquid capital to begin repeatable trade runs.",
        "sort_order": 10,
        "resources": (
            ("guide", "First Five Hours: Unlock the Trade Loop", 10),
            ("internal", "/forum", "Ask the fleet", "Verify current routes and prices before committing capital.", 20),
        ),
    },
    {
        "title": "Phase 2 · Day one: establish the Russia trade loop",
        "body": "Use a short, repeatable trade route and aim for Russia as the first economic platform. Keep a reserve instead of spending every coin on the hull.",
        "sort_order": 20,
        "resources": (
            ("guide", "Trade Route Safety and Capital Discipline", 10),
            ("build", "Starter Template: Russia Trade Runner", 20),
        ),
    },
    {
        "title": "Phase 3 · Day two and three: Essex plus mobility",
        "body": "Repeat the trade loop before buying Essex, then prioritize a fast travel ship such as La Creole so movement no longer consumes the whole session.",
        "sort_order": 30,
        "resources": (
            ("guide", "Day 1–3 Progression: Russia, Essex and La Creole", 10),
            ("build", "Starter Template: Essex Progression Frigate", 20),
            ("build", "Starter Template: La Creole Courier", 30),
        ),
    },
    {
        "title": "Phase 4 · Poltava training",
        "body": "Use Poltava to learn positioning, broadside timing, ammunition discipline and repair timing before moving into fleet-line ships.",
        "sort_order": 40,
        "resources": (
            ("guide", "Mid and Late Progression: Poltava to Victory", 10),
            ("build", "Starter Template: Poltava Gunnery", 20),
            ("internal", "/calendar", "Join a training event", "Use the calendar to find training and organized operations.", 30),
        ),
    },
    {
        "title": "Phase 5 · Victory and fleet-line readiness",
        "body": "Ownership is not readiness. Copy the announced fleet setup, join voice for competitive operations and confirm supplies before the event starts.",
        "sort_order": 50,
        "resources": (
            ("build", "Starter Template: Victory Fleet Line", 10),
            ("internal", "/squads", "Find your squad", "Coordinate with your permanent unit and its leadership.", 20),
        ),
    },
)


def _admin(db: Session) -> User | None:
    return db.scalar(
        select(User)
        .join(User.site_role)
        .where(SiteRoleDefinition.code == "admin", User.is_active.is_(True))
        .order_by(User.id)
    )


def _resource_from_spec(
    spec: tuple,
    guides: dict[str, Guide],
    builds: dict[str, Build],
) -> NewcomerGuideResource | None:
    resource_type = spec[0]
    if resource_type == "guide":
        guide = guides.get(spec[1])
        return (
            NewcomerGuideResource(resource_type="guide", resource_id=guide.id, sort_order=spec[2])
            if guide
            else None
        )
    if resource_type == "build":
        build = builds.get(spec[1])
        return (
            NewcomerGuideResource(resource_type="build", resource_id=build.id, sort_order=spec[2])
            if build
            else None
        )
    if resource_type == "internal":
        return NewcomerGuideResource(
            resource_type="internal",
            url=spec[1],
            label=spec[2],
            description=spec[3],
            sort_order=spec[4],
        )
    return None


def seed_newcomer_guide(db: Session) -> None:
    admin = _admin(db)
    guides = {
        guide.title: guide
        for guide in db.scalars(select(Guide).where(Guide.is_published.is_(True))).all()
    }
    builds = {
        build.build_name: build
        for build in db.scalars(select(Build).where(Build.is_official_template.is_(True))).all()
    }

    page = db.get(NewcomerGuidePage, 1)
    if page is None:
        page = NewcomerGuidePage(
            id=1,
            title="New Captain Guide",
            intro=PROGRESSION_INTRO,
            updated_by_id=admin.id if admin else None,
        )
        db.add(page)
        db.flush()
    else:
        # Retire only the untouched historic starter blocks. Custom blocks and
        # renamed/edited staff content remain untouched.
        page.blocks[:] = [
            block for block in page.blocks if block.title not in LEGACY_DEFAULT_BLOCK_TITLES
        ]
        if page.intro == LEGACY_DEFAULT_INTRO:
            page.intro = PROGRESSION_INTRO
            page.updated_by_id = admin.id if admin else page.updated_by_id

    existing_titles = {block.title for block in page.blocks}
    for block_data in PROGRESSION_BLOCKS:
        if block_data["title"] in existing_titles:
            continue
        block = NewcomerGuideBlock(
            block_type="resources",
            title=block_data["title"],
            body=block_data["body"],
            sort_order=block_data["sort_order"],
        )
        for spec in block_data["resources"]:
            resource = _resource_from_spec(spec, guides, builds)
            if resource is not None:
                block.resources.append(resource)
        page.blocks.append(block)
    db.commit()
