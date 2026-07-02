from sqlalchemy import text
from sqlalchemy.engine import Engine


SQLiteColumn = tuple[int, str, str, int, str | None, int]


def apply_lightweight_migrations(engine: Engine) -> None:
    """Tiny SQLite-friendly migrations for the MVP blueprint.

    This keeps local developer databases usable when a column is added before a real
    Alembic setup exists. Replace this with Alembic once schema evolution matters.
    """

    if not str(engine.url).startswith("sqlite"):
        return

    with engine.begin() as connection:
        users_columns = list(connection.execute(text("PRAGMA table_info(users)")))
        if users_columns and not _has_column(users_columns, "role"):
            connection.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(30) NOT NULL DEFAULT 'member'"))

        groups_columns = list(connection.execute(text("PRAGMA table_info(groups)")))
        if groups_columns:
            _add_column_if_missing(connection, "groups", groups_columns, "focus", "VARCHAR(40)", "pve_general", not_null=True)
            _add_column_if_missing(connection, "groups", groups_columns, "min_ship_rate", "INTEGER")
            _add_column_if_missing(connection, "groups", groups_columns, "allow_anonymous", "BOOLEAN", "1", not_null=True)
            _add_column_if_missing(connection, "groups", groups_columns, "fleet_restriction", "VARCHAR(120)")
            _add_column_if_missing(connection, "groups", groups_columns, "active", "BOOLEAN", "1", not_null=True)
            _add_column_if_missing(connection, "groups", groups_columns, "updated_at", "DATETIME")
            _add_column_if_missing(connection, "groups", groups_columns, "expires_at", "DATETIME")
            _add_column_if_missing(connection, "groups", groups_columns, "closed_at", "DATETIME")
            _add_column_if_missing(connection, "groups", groups_columns, "archived_at", "DATETIME")
            connection.execute(
                text(
                    "UPDATE groups "
                    "SET expires_at = COALESCE(expires_at, datetime(COALESCE(created_at, 'now'), '+24 hours')), "
                    "updated_at = COALESCE(updated_at, COALESCE(created_at, datetime('now')))"
                )
            )

        participants_columns = list(connection.execute(text("PRAGMA table_info(group_participants)")))
        if participants_columns:
            _add_column_if_missing(connection, "group_participants", participants_columns, "is_anonymous", "BOOLEAN", "0", not_null=True)
            _add_column_if_missing(connection, "group_participants", participants_columns, "anonymous_edit_token_hash", "VARCHAR(120)")
            _add_column_if_missing(connection, "group_participants", participants_columns, "fleet_name", "VARCHAR(120)")
            _add_column_if_missing(connection, "group_participants", participants_columns, "participant_role", "VARCHAR(40)")
            _add_column_if_missing(connection, "group_participants", participants_columns, "ship_id", "INTEGER")
            _add_column_if_missing(connection, "group_participants", participants_columns, "custom_ship_name", "VARCHAR(120)")
            _add_column_if_missing(connection, "group_participants", participants_columns, "custom_ship_rate", "INTEGER")
            _add_column_if_missing(connection, "group_participants", participants_columns, "note", "TEXT")
            _add_column_if_missing(connection, "group_participants", participants_columns, "active", "BOOLEAN", "1", not_null=True)
            _add_column_if_missing(connection, "group_participants", participants_columns, "joined_at", "DATETIME")
            _add_column_if_missing(connection, "group_participants", participants_columns, "left_at", "DATETIME")
            _add_column_if_missing(connection, "group_participants", participants_columns, "updated_at", "DATETIME")
            connection.execute(
                text(
                    "UPDATE group_participants "
                    "SET joined_at = COALESCE(joined_at, COALESCE(created_at, datetime('now'))), "
                    "updated_at = COALESCE(updated_at, COALESCE(created_at, datetime('now'))), "
                    "is_anonymous = CASE WHEN user_id IS NULL THEN 1 ELSE is_anonymous END"
                )
            )

        builds_columns = list(connection.execute(text("PRAGMA table_info(builds)")))
        if builds_columns:
            _add_column_if_missing(connection, "builds", builds_columns, "purpose", "VARCHAR(80)", "Allround", not_null=True)
            _add_column_if_missing(connection, "builds", builds_columns, "build_role", "VARCHAR(40)")
            _add_column_if_missing(connection, "builds", builds_columns, "cannon_setup", "TEXT", "", not_null=True)
            _add_column_if_missing(connection, "builds", builds_columns, "weapon_bow_setup", "TEXT", "", not_null=True)
            _add_column_if_missing(connection, "builds", builds_columns, "weapon_port_setup", "TEXT", "", not_null=True)
            _add_column_if_missing(connection, "builds", builds_columns, "weapon_starboard_setup", "TEXT", "", not_null=True)
            _add_column_if_missing(connection, "builds", builds_columns, "weapon_stern_setup", "TEXT", "", not_null=True)
            _add_column_if_missing(connection, "builds", builds_columns, "sail_setup", "TEXT", "", not_null=True)
            _add_column_if_missing(connection, "builds", builds_columns, "upgrade_setup", "TEXT", "", not_null=True)
            _add_column_if_missing(connection, "builds", builds_columns, "crew_target", "INTEGER")
            _add_column_if_missing(connection, "builds", builds_columns, "crew_gunnery", "INTEGER")
            _add_column_if_missing(connection, "builds", builds_columns, "crew_sailing", "INTEGER")
            _add_column_if_missing(connection, "builds", builds_columns, "crew_repair", "INTEGER")
            _add_column_if_missing(connection, "builds", builds_columns, "crew_boarding", "INTEGER")
            _add_column_if_missing(connection, "builds", builds_columns, "crew_setup", "TEXT", "", not_null=True)
            _add_column_if_missing(connection, "builds", builds_columns, "special_crew_setup", "TEXT", "", not_null=True)
            _add_column_if_missing(connection, "builds", builds_columns, "cargo_setup", "TEXT", "", not_null=True)
            _add_column_if_missing(connection, "builds", builds_columns, "ammunition_setup", "TEXT", "", not_null=True)
            _add_column_if_missing(connection, "builds", builds_columns, "consumable_setup", "TEXT", "", not_null=True)
            _add_column_if_missing(connection, "builds", builds_columns, "tactics", "TEXT", "", not_null=True)

            refreshed_builds_columns = list(connection.execute(text("PRAGMA table_info(builds)")))
            if _has_column(refreshed_builds_columns, "focus") and _has_column(refreshed_builds_columns, "purpose"):
                connection.execute(
                    text("UPDATE builds SET purpose = focus WHERE purpose = 'Allround' AND focus IS NOT NULL AND focus != ''")
                )


def _add_column_if_missing(
    connection,
    table_name: str,
    columns: list[SQLiteColumn],
    name: str,
    column_type: str,
    default: str | None = None,
    *,
    not_null: bool = False,
) -> None:
    if _has_column(columns, name):
        return

    default_clause = ""
    if default is not None:
        if default in {"0", "1"} and column_type.upper() == "BOOLEAN":
            default_clause = f" DEFAULT {default}"
        else:
            safe_default = default.replace("'", "''")
            default_clause = f" DEFAULT '{safe_default}'"
    not_null_clause = " NOT NULL" if not_null else ""
    connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {name} {column_type}{not_null_clause}{default_clause}"))


def _has_column(columns: list[SQLiteColumn], name: str) -> bool:
    return any(column[1] == name for column in columns)
