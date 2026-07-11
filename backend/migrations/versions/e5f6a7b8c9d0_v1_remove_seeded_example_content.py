"""remove pre-v1 seeded example content

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-11
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STARTER_BUILD_TITLES = (
    "Starter Template: Russia Trade Runner",
    "Starter Template: Essex Progression Frigate",
    "Starter Template: La Creole Courier",
    "Starter Template: Poltava Gunnery",
    "Starter Template: Victory Fleet Line",
)
STARTER_GUIDE_TITLES = (
    "First Five Hours: Unlock the Trade Loop",
    "Day 1–3 Progression: Russia, Essex and La Creole",
    "Mid and Late Progression: Poltava to Victory",
    "Trade Route Safety and Capital Discipline",
)
SEEDED_NEWCOMER_BLOCK_TITLES = (
    "Welcome aboard",
    "Your first route",
    "Competitive operations",
    "Phase 1 · First five hours",
    "Phase 2 · Day one: establish the Russia trade loop",
    "Phase 3 · Day two and three: Essex plus mobility",
    "Phase 4 · Poltava training",
    "Phase 5 · Victory and fleet-line readiness",
)
SEEDED_NEWCOMER_INTROS = (
    "A curated route from your first login to confident fleet participation. Work through the sections in order, ask questions early and check the calendar before joining operations.",
    "A practical progression route from the first login through trade, early frigates, mobility, Poltava training and eventual fleet-line readiness. Economy values are targets, not guarantees.",
)

LEGACY_GROUPS = {
    "Evening PvE Farming Run": "Relaxed fleet announcement for resources",
    "Arena Practice Rotation": "Practice announcement for arena rotations",
}
LEGACY_EVENTS = {
    "Port Battle Briefing": "Fleet briefing, role assignment",
    "Gunnery Training": "Short practice block for arcs",
    "Fleet Farm Run": "Relaxed resource and XP farming round",
}
LEGACY_THREADS = {
    "Practice feedback: line turns and repair cadence": "Last training showed better focus fire",
    "Weekly logistics: escort slots for trade convoy": "The trade fleet is collecting escort availability",
}
LEGACY_GUIDES = {
    "Port-Battle Line Basics": "A compact starter doctrine for line discipline",
    "Trade Convoy Checklist": "A practical checklist for safe fleet trade runs",
}
LEGACY_BUILDS = {
    "Victory Defensive Line": "Demo build for line/sustain play.",
    "Surprise Gunnery Scout": "Fast sample build for scouting",
    "Adventure Mortar Support": "Siege sample build",
}
LEGACY_FILE_PATHS = ("demo/line-battle.svg", "demo/trade-convoy.svg")


def _ids_for_values(connection, table: str, column: str, values: Iterable[str]) -> list[int]:
    values = tuple(values)
    if not values:
        return []
    statement = sa.text(f"SELECT id FROM {table} WHERE {column} IN :values").bindparams(
        sa.bindparam("values", expanding=True)
    )
    return [int(row[0]) for row in connection.execute(statement, {"values": values})]


def _ids_for_markers(
    connection,
    *,
    table: str,
    title_column: str,
    marker_column: str,
    markers: dict[str, str],
) -> list[int]:
    ids: list[int] = []
    statement = sa.text(
        f"SELECT id FROM {table} "
        f"WHERE {title_column} = :title AND {marker_column} LIKE :marker"
    )
    for title, marker in markers.items():
        ids.extend(
            int(row[0])
            for row in connection.execute(
                statement,
                {"title": title, "marker": f"%{marker}%"},
            )
        )
    return ids


def _delete_ids(connection, table: str, column: str, ids: Iterable[int]) -> None:
    ids = tuple(ids)
    if not ids:
        return
    statement = sa.text(f"DELETE FROM {table} WHERE {column} IN :ids").bindparams(
        sa.bindparam("ids", expanding=True)
    )
    connection.execute(statement, {"ids": ids})


def _clear_build_references(connection, build_ids: list[int]) -> None:
    if not build_ids:
        return
    statement = sa.text(
        "UPDATE group_members SET build_id = NULL WHERE build_id IN :ids"
    ).bindparams(sa.bindparam("ids", expanding=True))
    connection.execute(statement, {"ids": build_ids})
    resource_statement = sa.text(
        "DELETE FROM newcomer_guide_resources "
        "WHERE resource_type = 'build' AND resource_id IN :ids"
    ).bindparams(sa.bindparam("ids", expanding=True))
    connection.execute(resource_statement, {"ids": build_ids})
    _delete_ids(connection, "guide_build_references", "build_id", build_ids)
    _delete_ids(connection, "build_slots", "build_id", build_ids)


def _delete_guides(connection, guide_ids: list[int]) -> None:
    if not guide_ids:
        return
    resource_statement = sa.text(
        "DELETE FROM newcomer_guide_resources "
        "WHERE resource_type = 'guide' AND resource_id IN :ids"
    ).bindparams(sa.bindparam("ids", expanding=True))
    connection.execute(resource_statement, {"ids": guide_ids})
    _delete_ids(connection, "guide_attachments", "guide_id", guide_ids)
    _delete_ids(connection, "guide_build_references", "guide_id", guide_ids)
    _delete_ids(connection, "guides", "id", guide_ids)


def _delete_forum_threads(connection, thread_ids: list[int]) -> None:
    if not thread_ids:
        return
    post_ids_statement = sa.text(
        "SELECT id FROM forum_posts WHERE thread_id IN :ids"
    ).bindparams(sa.bindparam("ids", expanding=True))
    post_ids = [
        int(row[0]) for row in connection.execute(post_ids_statement, {"ids": thread_ids})
    ]
    _delete_ids(connection, "forum_post_attachments", "post_id", post_ids)
    _delete_ids(connection, "forum_posts", "thread_id", thread_ids)
    _delete_ids(connection, "forum_threads", "id", thread_ids)


def upgrade() -> None:
    connection = op.get_bind()

    starter_build_ids = _ids_for_values(
        connection, "builds", "build_name", STARTER_BUILD_TITLES
    )
    legacy_build_ids = _ids_for_markers(
        connection,
        table="builds",
        title_column="build_name",
        marker_column="details",
        markers=LEGACY_BUILDS,
    )
    build_ids = sorted(set(starter_build_ids + legacy_build_ids))
    _clear_build_references(connection, build_ids)
    _delete_ids(connection, "builds", "id", build_ids)

    starter_guide_ids = _ids_for_values(connection, "guides", "title", STARTER_GUIDE_TITLES)
    legacy_guide_ids = _ids_for_markers(
        connection,
        table="guides",
        title_column="title",
        marker_column="summary",
        markers=LEGACY_GUIDES,
    )
    _delete_guides(connection, sorted(set(starter_guide_ids + legacy_guide_ids)))

    group_ids = _ids_for_markers(
        connection,
        table="groups",
        title_column="title",
        marker_column="description",
        markers=LEGACY_GROUPS,
    )
    _delete_ids(connection, "group_members", "group_id", group_ids)
    _delete_ids(connection, "groups", "id", group_ids)

    event_ids = _ids_for_markers(
        connection,
        table="fleet_events",
        title_column="title",
        marker_column="description",
        markers=LEGACY_EVENTS,
    )
    _delete_ids(connection, "fleet_events", "id", event_ids)

    thread_ids: list[int] = []
    thread_statement = sa.text(
        "SELECT DISTINCT forum_threads.id "
        "FROM forum_threads JOIN forum_posts ON forum_posts.thread_id = forum_threads.id "
        "WHERE forum_threads.title = :title AND forum_posts.body LIKE :marker"
    )
    for title, marker in LEGACY_THREADS.items():
        thread_ids.extend(
            int(row[0])
            for row in connection.execute(
                thread_statement,
                {"title": title, "marker": f"%{marker}%"},
            )
        )
    _delete_forum_threads(connection, sorted(set(thread_ids)))

    block_ids = _ids_for_values(
        connection,
        "newcomer_guide_blocks",
        "title",
        SEEDED_NEWCOMER_BLOCK_TITLES,
    )
    _delete_ids(connection, "newcomer_guide_resources", "block_id", block_ids)
    _delete_ids(connection, "newcomer_guide_blocks", "id", block_ids)

    intro_statement = sa.text(
        "UPDATE newcomer_guide_pages SET intro = '' WHERE intro IN :intros"
    ).bindparams(sa.bindparam("intros", expanding=True))
    connection.execute(intro_statement, {"intros": SEEDED_NEWCOMER_INTROS})

    file_ids = _ids_for_values(
        connection, "stored_files", "relative_path", LEGACY_FILE_PATHS
    )
    _delete_ids(connection, "guide_attachments", "file_id", file_ids)
    _delete_ids(connection, "forum_post_attachments", "file_id", file_ids)
    _delete_ids(connection, "stored_files", "id", file_ids)


def downgrade() -> None:
    # Example content is intentionally not recreated. Downgrading the schema
    # does not reinsert user-facing data that v1 removed.
    pass
