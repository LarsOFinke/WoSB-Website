from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounts.models.user import User
from app.modules.builds.models.build import Build
from app.modules.builds.schemas.build_create import BuildCreate
from app.modules.builds.services.build_service import BuildValidationError, create_build
from app.modules.guides.models.guide import Guide
from app.modules.guides.models.guide_build_reference import GuideBuildReference
from app.modules.permissions.models.role import SiteRoleDefinition
from app.modules.ships.models.ship import Ship


STARTER_BUILD_DATA = (
    {
        "build_name": "Starter Template: Russia Trade Runner",
        "ship_name": "Russia",
        "build_type": "balanced",
        "sails": "Stitched Sails",
        "upgrade_1": "Double Hold",
        "upgrade_2": "Maneuverable Helm",
        "upgrade_3": "Lightweight Hull",
        "lantern": "Golden Lantern",
        "sailors": 43,
        "soldiers": 15,
        "musketeers": 25,
        "mercenaries": 5,
        "rear_weapon_slots": [{"item": "Twin 6-pdr", "quantity": 2}],
        "port_weapon_slots": [{"item": "16-pdr Cannon", "quantity": 14}],
        "starboard_weapon_slots": [{"item": "16-pdr Cannon", "quantity": 14}],
        "details": "Official progression template for early trade runs. Adjust cargo and protection to the current route and risk level.",
    },
    {
        "build_name": "Starter Template: Essex Progression Frigate",
        "ship_name": "Essex",
        "build_type": "balanced",
        "sails": "Stitched Sails",
        "upgrade_1": "Reinforced Ports",
        "upgrade_2": "Maneuverable Helm",
        "upgrade_3": "Repair Arsenal",
        "lantern": "Blue Lantern",
        "sailors": 54,
        "soldiers": 24,
        "musketeers": 38,
        "mercenaries": 8,
        "front_weapon_slots": [{"item": "Twin 14-pdr", "quantity": 2}],
        "rear_weapon_slots": [{"item": "Twin 14-pdr", "quantity": 2}],
        "port_weapon_slots": [{"item": "24-pdr Carronade", "quantity": 21}],
        "starboard_weapon_slots": [{"item": "24-pdr Carronade", "quantity": 21}],
        "details": "Official early combat template. Use it as a safe baseline and adapt ammunition to the planned activity.",
    },
    {
        "build_name": "Starter Template: La Creole Courier",
        "ship_name": "La Creole",
        "build_type": "balanced",
        "sails": "Elite Sails",
        "upgrade_1": "Maneuverable Helm",
        "upgrade_2": "Lightweight Hull",
        "upgrade_3": "Copper Plating",
        "lantern": "Red Lantern",
        "sailors": 38,
        "soldiers": 12,
        "musketeers": 28,
        "mercenaries": 6,
        "rear_weapon_slots": [{"item": "Twin 6-pdr", "quantity": 4}],
        "port_weapon_slots": [{"item": "16-pdr Culverin", "quantity": 12}],
        "starboard_weapon_slots": [{"item": "16-pdr Culverin", "quantity": 12}],
        "details": "Official mobility template for travelling, scouting and moving between activities quickly.",
    },
    {
        "build_name": "Starter Template: Poltava Gunnery",
        "ship_name": "Poltava",
        "build_type": "gunnery",
        "sails": "Tarpaulin Sails",
        "upgrade_1": "Ammunition Cradles",
        "upgrade_2": "Reinforced Ports",
        "upgrade_3": "Repair Arsenal",
        "lantern": "Golden Lantern",
        "sailors": 53,
        "soldiers": 28,
        "musketeers": 40,
        "mercenaries": 8,
        "front_weapon_slots": [{"item": "Twin 14-pdr", "quantity": 4}],
        "port_weapon_slots": [{"item": "32-pdr Cannon", "quantity": 23}],
        "starboard_weapon_slots": [{"item": "32-pdr Cannon", "quantity": 23}],
        "details": "Official mid-progression gunnery baseline for learning positioning and sustained broadsides.",
    },
    {
        "build_name": "Starter Template: Victory Fleet Line",
        "ship_name": "Victory",
        "build_type": "defensive",
        "sails": "Tarpaulin Sails",
        "upgrade_1": "Structural Expansion",
        "upgrade_2": "Sturdy Frames",
        "upgrade_3": "Strong Beams",
        "upgrade_4": "Repair Arsenal",
        "upgrade_5": "Reinforced Ports",
        "lantern": "Golden Lantern",
        "sailors": 82,
        "soldiers": 42,
        "musketeers": 56,
        "mercenaries": 18,
        "front_weapon_slots": [{"item": "Twin 20-pdr", "quantity": 4}],
        "rear_weapon_slots": [{"item": "Twin 20-pdr", "quantity": 4}],
        "port_weapon_slots": [{"item": "42-pdr Carronade", "quantity": 49}],
        "starboard_weapon_slots": [{"item": "42-pdr Carronade", "quantity": 49}],
        "details": "Official late-progression line template. Competitive operations may require a fleet-specific variation.",
    },
)

GUIDE_DATA = (
    {
        "title": "First Five Hours: Unlock the Trade Loop",
        "category": "training",
        "summary": "A practical first-session checklist that prioritizes navigation, starter capital and repeatable trade routes.",
        "body": (
            "## Goal\n"
            "Use the first five hours to learn controls, complete the earliest reliable activities and build enough liquid capital for trade runs.\n\n"
            "## Checklist\n"
            "1. Finish the introductory tasks and avoid expensive experimental purchases.\n"
            "2. Learn one short, low-risk trade route before expanding to longer routes.\n"
            "3. Keep a cash reserve for cargo replacement and repairs.\n"
            "4. Ask the fleet for current market checks; route profit changes with prices and risk.\n\n"
            "The often-quoted 200–300k daily target is a planning range, not a guarantee. Market prices, travel time and losses can change the result."
        ),
        "build_names": (),
    },
    {
        "title": "Day 1–3 Progression: Russia, Essex and La Creole",
        "category": "training",
        "summary": "A staged early progression path combining economy, a first fighting frigate and a fast travel ship.",
        "body": (
            "## Day 1\n"
            "Start with the trade loop and aim for Russia as the first economic platform. Use the official Russia template as a baseline.\n\n"
            "## Day 2\n"
            "Run the route again before spending. Build the reserve for Essex and keep enough capital to continue trading after the purchase.\n\n"
            "## Day 3\n"
            "Prioritize mobility. Work toward La Creole so moving between ports, groups and events stops consuming most of the session.\n\n"
            "Progression is intentionally flexible: do not force a purchase when the market or your available playtime makes it unsafe."
        ),
        "build_names": (
            "Starter Template: Russia Trade Runner",
            "Starter Template: Essex Progression Frigate",
            "Starter Template: La Creole Courier",
        ),
    },
    {
        "title": "Mid and Late Progression: Poltava to Victory",
        "category": "training",
        "summary": "How to move from early frigates into sustained gunnery and fleet-line responsibilities.",
        "body": (
            "Use Poltava to practice positioning, broadside timing and repair discipline before committing to the cost and responsibility of Victory. "
            "Do not treat ship ownership as readiness: join training events, copy the announced fleet build and confirm ammunition and voice requirements before competitive operations."
        ),
        "build_names": (
            "Starter Template: Poltava Gunnery",
            "Starter Template: Victory Fleet Line",
        ),
    },
    {
        "title": "Trade Route Safety and Capital Discipline",
        "category": "logistics",
        "summary": "Risk controls for turning trade routes into repeatable progression instead of a single all-in gamble.",
        "body": (
            "Never place all available capital into one cargo run. Verify both ends of the route, keep repair money, prefer a route you can repeat, and stop when losses would block the next ship goal. "
            "Share current route information in the fleet rather than treating an old price screenshot as permanent."
        ),
        "build_names": ("Starter Template: Russia Trade Runner",),
    },
)


def _admin_user(db: Session) -> User | None:
    return db.scalar(
        select(User)
        .join(User.site_role)
        .where(SiteRoleDefinition.code == "admin", User.is_active.is_(True))
        .order_by(User.id)
    )


def _payload(row: dict[str, object], ship_id: int) -> BuildCreate:
    values = {
        "build_name": row["build_name"],
        "build_type": row.get("build_type", "balanced"),
        "ship_id": ship_id,
        "sails": row.get("sails"),
        "upgrade_1": row.get("upgrade_1"),
        "upgrade_2": row.get("upgrade_2"),
        "upgrade_3": row.get("upgrade_3"),
        "upgrade_4": row.get("upgrade_4"),
        "upgrade_5": row.get("upgrade_5"),
        "upgrade_6": row.get("upgrade_6"),
        "lantern": row.get("lantern"),
        "sailors": row.get("sailors", 0),
        "soldiers": row.get("soldiers", 0),
        "musketeers": row.get("musketeers", 0),
        "mercenaries": row.get("mercenaries", 0),
        "front_weapon_slots": row.get("front_weapon_slots", []),
        "rear_weapon_slots": row.get("rear_weapon_slots", []),
        "port_weapon_slots": row.get("port_weapon_slots", []),
        "starboard_weapon_slots": row.get("starboard_weapon_slots", []),
        "mortar_weapon_slots": row.get("mortar_weapon_slots", []),
        "special_crew_slots": row.get("special_crew_slots", []),
        "ammunition_slots": row.get("ammunition_slots", []),
        "consumable_slots": row.get("consumable_slots", []),
        "hold_slots": row.get("hold_slots", []),
        "details": row.get("details"),
    }
    return BuildCreate(**values)


def _sync_build_references(guide: Guide, build_names: tuple[str, ...], builds: dict[str, Build]) -> None:
    current = {reference.build_id: reference for reference in guide.build_references}
    active_build_ids: set[int] = set()
    for index, name in enumerate(build_names, start=1):
        build = builds[name]
        active_build_ids.add(build.id)
        reference = current.get(build.id)
        if reference is None:
            guide.build_references.append(
                GuideBuildReference(build_id=build.id, sort_order=index * 10)
            )
        else:
            reference.sort_order = index * 10
    for reference in list(guide.build_references):
        if reference.build_id not in active_build_ids:
            guide.build_references.remove(reference)


def seed_starter_content(db: Session) -> None:
    admin = _admin_user(db)
    if admin is None:
        return

    ships = {ship.name: ship for ship in db.scalars(select(Ship).where(Ship.is_active.is_(True))).all()}
    builds: dict[str, Build] = {}
    for row in STARTER_BUILD_DATA:
        name = str(row["build_name"])
        existing = db.scalar(select(Build).where(Build.build_name == name, Build.is_official_template.is_(True)))
        if existing is None:
            ship = ships.get(str(row["ship_name"]))
            if ship is None:
                raise RuntimeError(f"Starter build ship is missing: {row['ship_name']}")
            try:
                existing = create_build(db, _payload(row, ship.id), owner_id=admin.id)
            except BuildValidationError as exc:
                raise RuntimeError(f"Starter build seed failed for {name}: {exc}") from exc
            existing.is_official_template = True
            db.commit()
            db.refresh(existing)
        builds[name] = existing

    for row in GUIDE_DATA:
        title = str(row["title"])
        guide = db.scalar(select(Guide).where(Guide.title == title))
        if guide is None:
            guide = Guide(title=title, owner_id=admin.id, body="")
            db.add(guide)
            db.flush()
        guide.category = str(row["category"])
        guide.summary = str(row["summary"])
        guide.body = str(row["body"])
        guide.owner_id = admin.id
        guide.is_published = True
        _sync_build_references(guide, tuple(row["build_names"]), builds)
    db.commit()
