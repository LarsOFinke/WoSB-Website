from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.base import Base
from app.modules.accounts.models.user import User


_RELATED_TABLES: tuple[tuple[str, str], ...] = (
    ("user_profiles", "user_id"),
    ("user_profile_ship_preferences", "user_id"),
    ("user_profile_role_preferences", "user_id"),
    ("auth_sessions", "user_id"),
    ("registration_requests", "created_user_id"),
    ("cookie_consent_decisions", "user_id"),
    ("fleet_memberships", "user_id"),
    ("stored_files", "owner_id"),
    ("builds", "owner_id"),
    ("build_votes", "user_id"),
    ("guides", "owner_id"),
    ("forum_threads", "owner_id"),
    ("forum_posts", "author_id"),
    ("fleet_events", "owner_id"),
    ("squads", "created_by_id"),
    ("groups", "owner_id"),
    ("group_members", "user_id"),
    ("audit_logs", "actor_user_id"),
    ("data_subject_requests", "subject_user_id"),
    ("privacy_contact_requests", "user_id"),
)
_SECRET_COLUMNS = {"password_hash", "token_hash", "consent_key"}


def _json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return "[binary omitted]"
    return value


def _safe_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: _json_value(value) for key, value in row.items() if key not in _SECRET_COLUMNS}


class PersonalDataExportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def build(self, user: User) -> dict[str, Any]:
        account = {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        }
        categories: dict[str, list[dict[str, Any]]] = {}
        metadata = Base.metadata
        for table_name, owner_column in _RELATED_TABLES:
            table = metadata.tables.get(table_name)
            if table is None or owner_column not in table.c:
                raise RuntimeError(
                    f"Personal data export mapping is stale: {table_name}.{owner_column}"
                )
            rows = self.db.execute(select(table).where(table.c[owner_column] == user.id)).mappings()
            categories[table_name] = [_safe_row(dict(row)) for row in rows]
        return {
            "schema_version": 1,
            "exported_at": utc_now().isoformat(),
            "subject": account,
            "categories": categories,
            "exclusions": [
                "password hashes, session token hashes and consent identifiers",
                "data belonging to other users",
                "server secrets and internal cryptographic material",
            ],
        }
