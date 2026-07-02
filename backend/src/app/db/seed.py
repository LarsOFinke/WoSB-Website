from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import engine
from app.models import Build, BuildOption, Group, GroupParticipant, Profile, Ship, User

from app.db.seeds import SHIP_SEED_DATA, SOURCE_NOTE_FULL, SOURCE_NOTE_PARTIAL, SOURCE_URL
from app.db.seeds.build_option_seed_data import BUILD_OPTION_SEED_DATA


def seed_database(db: Session, *, reset: bool = False) -> None:
    if reset:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    _seed_ships(db)
    _seed_build_options(db)
    admin_user = _seed_demo_user(db)
    member_user = _seed_member_user(db)
    _seed_demo_groups(db, admin_user, member_user)
    _seed_demo_builds(db, admin_user, member_user)
    db.commit()


def _seed_ships(db: Session) -> None:
    existing_count = db.scalar(select(func.count()).select_from(Ship)) or 0
    if existing_count:
        return

    for raw in SHIP_SEED_DATA:
        full_stats_available = raw.get("durability") is not None
        data = {
            **raw,
            "speed": Decimal(raw["speed"]) if raw.get("speed") is not None else None,
            "armor": Decimal(raw["armor"]) if raw.get("armor") is not None else None,
            "source_url": SOURCE_URL,
            "source_note": SOURCE_NOTE_FULL if full_stats_available else SOURCE_NOTE_PARTIAL,
        }
        db.add(Ship(**data))
    db.flush()


def _seed_build_options(db: Session) -> None:
    existing_count = db.scalar(select(func.count()).select_from(BuildOption)) or 0
    if existing_count:
        return

    db.add_all(BuildOption(**raw) for raw in BUILD_OPTION_SEED_DATA)
    db.flush()


def _seed_demo_user(db: Session) -> User:
    existing = db.scalars(select(User).where(User.username == "demo")).first()
    if existing:
        existing.role = "admin"
        return existing

    user = User(
        username="demo",
        password_hash=hash_password("demo123"),
        display_name="Demo Admin",
        role="admin",
    )
    db.add(user)
    db.flush()
    db.add(
        Profile(
            user_id=user.id,
            main_role="Kapitän",
            fleet_name="WoSB Administration",
            bio="Webseiten-Administrator mit Zugriff auf alle Gruppen.",
        )
    )
    db.flush()
    return user


def _seed_member_user(db: Session) -> User:
    existing = db.scalars(select(User).where(User.username == "captain")).first()
    if existing:
        existing.role = "member"
        return existing

    user = User(
        username="captain",
        password_hash=hash_password("captain123"),
        display_name="Captain Beispiel",
        role="member",
    )
    db.add(user)
    db.flush()
    db.add(
        Profile(
            user_id=user.id,
            main_role="Gruppenleiter",
            fleet_name="WoSB",
            bio="Normaler Benutzer, der nur eigene Gruppen verwalten darf.",
        )
    )
    db.flush()
    return user


def _seed_demo_groups(db: Session, admin_user: User, member_user: User) -> None:
    existing_count = db.scalar(select(func.count()).select_from(Group)) or 0
    if existing_count:
        return

    victory = db.scalars(select(Ship).where(Ship.name == "Victory")).first()
    horizont = db.scalars(select(Ship).where(Ship.name == "Horizont")).first()
    constitution = db.scalars(select(Ship).where(Ship.name == "Constitution")).first()

    group_one = Group(
        owner_id=admin_user.id,
        ship_id=victory.id if victory else None,
        ship_class_label="Ship of the Line",
        title="Imp-Hunting Linie am Abend",
        description=(
            "Koordinierte PvE-Jagd auf schwere Ziele. Bitte Reparaturmaterial mitbringen, "
            "Fokusfeuer halten und im Voice erreichbar sein."
        ),
        focus="pve_imp_hunting",
        max_members=8,
        min_ship_rate=3,
        allow_anonymous=True,
        fleet_restriction=None,
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    group_two = Group(
        owner_id=member_user.id,
        ship_id=horizont.id if horizont else None,
        ship_class_label="Brigantine",
        title="Einsteigertraining: Segel, Rollen, Fokusfeuer",
        description=(
            "Ruhige Trainingsrunde für neue Captains. Wir üben Formationsfahrt, Zielansagen, "
            "Munitionswechsel und sicheres Zurückziehen."
        ),
        focus="pve_general",
        max_members=5,
        min_ship_rate=7,
        allow_anonymous=True,
        fleet_restriction="Keine feste Flotte nötig",
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=2),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    group_three = Group(
        owner_id=admin_user.id,
        ship_id=constitution.id if constitution else None,
        ship_class_label="Frigate",
        title="Open-World PvP Scout-Runde",
        description=(
            "Kleine bewegliche Gruppe für Aufklärung und kurze Gefechte. Bitte nur beitreten, "
            "wenn du schnell reagieren und auch abbrechen kannst."
        ),
        focus="pvp_open_world",
        max_members=4,
        min_ship_rate=5,
        allow_anonymous=False,
        fleet_restriction="WoSB oder eingeladene Gäste",
        scheduled_at=datetime.now(timezone.utc) + timedelta(hours=6),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add_all([group_one, group_two, group_three])
    db.flush()
    db.add_all(
        [
            GroupParticipant(
                group_id=group_one.id,
                user_id=admin_user.id,
                is_anonymous=False,
                display_name=admin_user.display_name,
                fleet_name="WoSB Administration",
                ship_id=victory.id if victory else None,
                participant_role="Leitung / Linie",
                status="member",
            ),
            GroupParticipant(
                group_id=group_one.id,
                is_anonymous=True,
                display_name="Navigatorin Ada",
                fleet_name="Freie Händler",
                custom_ship_name="Victory",
                custom_ship_rate=1,
                note="Kann bei Bedarf callen.",
                participant_role="Support / Calls",
                status="member",
            ),
            GroupParticipant(
                group_id=group_two.id,
                user_id=member_user.id,
                is_anonymous=False,
                display_name=member_user.display_name,
                fleet_name="WoSB",
                ship_id=horizont.id if horizont else None,
                participant_role="Training / Flex",
                status="member",
            ),
            GroupParticipant(
                group_id=group_two.id,
                is_anonymous=True,
                display_name="Gastspieler",
                custom_ship_name="Brig",
                custom_ship_rate=7,
                participant_role="Flex",
                status="member",
            ),
            GroupParticipant(
                group_id=group_three.id,
                user_id=admin_user.id,
                is_anonymous=False,
                display_name=admin_user.display_name,
                ship_id=constitution.id if constitution else None,
                participant_role="Scout",
                status="member",
            ),
        ]
    )
    db.flush()

def _seed_demo_builds(db: Session, admin_user: User, member_user: User) -> None:
    existing_count = db.scalar(select(func.count()).select_from(Build)) or 0
    if existing_count:
        return

    victory = db.scalars(select(Ship).where(Ship.name == "Victory")).first()
    pickle_ship = db.scalars(select(Ship).where(Ship.name == "Pickle")).first()

    db.add_all(
        [
            Build(
                author_id=admin_user.id,
                ship_id=victory.id if victory else None,
                ship_class_label="Ship of the Line",
                title="Victory Linienbrecher",
                purpose="Linienkampf / Gruppen-PvP",
                build_role="Tank / Linie",
                cannon_setup="Gesamt: Reichweite und konstantes Fokusfeuer priorisieren.",
                weapon_bow_setup="Bug: Long Cannons / Culverins als Chaser für Druck beim Anfahren.",
                weapon_port_setup="Backbord: Long Cannons / Culverins als Hauptbreitseite.",
                weapon_starboard_setup="Steuerbord: Long Cannons / Culverins als Hauptbreitseite.",
                weapon_stern_setup="Heck: Standard Cannons oder leichte Chaser für Rückzugsdruck.",
                sail_setup="Large Additional Sails für Positionskorrekturen und Rückzug aus schlechten Winkeln.",
                upgrade_setup="Slot 1: Structural Expansion\nSlot 2: Ammunition Cradles\nSlot 3 XP: Strong Frames\nSlot 4 XP: Repairs Arsenal\nSpecial: Durability Feintuning",
                crew_target=victory.crew if victory else None,
                crew_gunnery=86,
                crew_sailing=30,
                crew_repair=58,
                crew_boarding=30,
                crew_setup="Kanoniere und Reparaturcrew priorisieren; Boarding-Crew nur optional.",
                special_crew_setup="Repair Specialist; Gunnery Specialist; Old Hand für PvE-Sustain möglich.",
                cargo_setup="Reparaturmaterial, Ersatzplanken und genug Vorräte für längere Gefechte.",
                ammunition_setup="Schwere Kugeln als Standard; Kettenkugeln zum Öffnen von Fokuszielen; Kartätschen für Nahbereich/Boarding-Vorbereitung.",
                consumable_setup="Rum, Reparatur-Kits und Brandbekämpfung; Verbrauchsgüter auf längere Gefechte auslegen.",
                tactics="Mit der Linie fahren, Fokusfeuer halten und nicht allein drehen. Kettenkugeln auf schnelle Ziele, schwere Kugeln gegen Hauptziele.",
                notes="Solide Standardkonfiguration für koordinierte Gruppenfahrten.",
            ),
            Build(
                author_id=member_user.id,
                ship_id=pickle_ship.id if pickle_ship else None,
                ship_class_label="Schooner",
                title="Pickle Scout Starter",
                purpose="Aufklärung / Scout",
                build_role="Scout",
                cannon_setup="Gesamt: leichte Bewaffnung für Distanz, Störung und Fluchtfenster.",
                weapon_bow_setup="Bug: Long Cannons / Culverins für Chase und frühes Poken.",
                weapon_port_setup="Backbord: Standard Cannons leicht/mittel für kurze Störangriffe.",
                weapon_starboard_setup="Steuerbord: Standard Cannons leicht/mittel für kurze Störangriffe.",
                weapon_stern_setup="Heck: Long Cannons / Culverins oder leichte Chaser für Rückzug.",
                sail_setup="Small Additional Sails oder Elite Sails für Chase, Spotting und Rückzug.",
                upgrade_setup="Slot 1: Maneuverable Helm\nSlot 2: Lightweight Hull\nSlot 3 XP: Ammunition Cradles\nSlot 4 XP: Repairs Arsenal\nSpecial: Mobility Feintuning",
                crew_target=pickle_ship.crew if pickle_ship else None,
                crew_gunnery=18,
                crew_sailing=28,
                crew_repair=14,
                crew_boarding=6,
                crew_setup="Segelhandling und schnelle Reparaturen priorisieren; Boarding minimal halten.",
                special_crew_setup="Navigator / Helmsman; Explorer Crew; Repair Specialist optional.",
                cargo_setup="Leicht halten: Reparaturmaterial und wenig Handelsladung, damit Geschwindigkeit erhalten bleibt.",
                ammunition_setup="Kettenkugeln für Verfolgung und Flucht; leichte Kugeln für kurze Störangriffe.",
                consumable_setup="Segel-/Rumpfreparaturen und Notfall-Verbrauchsgüter für schnelle Rückzüge.",
                tactics="Aufklären, Gegner binden und Informationen liefern. Direkte Linienkämpfe meiden.",
                notes="Leichtes Einsteiger-Build für schnelle Orientierung und Support.",
            ),
        ]
    )
    db.flush()
