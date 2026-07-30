"""Separate free-compatible Raid-Helper payloads from Premium features.

Revision ID: 0020_raid_helper_premium
Revises: 0019_raid_helper_template_id
"""

from __future__ import annotations

import json

from alembic import op
import sqlalchemy as sa

revision: str = "0020_raid_helper_premium"
down_revision: str = "0019_raid_helper_template_id"
branch_labels = None
depends_on = None

_FREE_KEYS = {"title", "description", "date", "time", "duration", "leaderId"}
_FREE_PAYLOAD = {
    "title": "{{rendered.title}}",
    "description": "{{rendered.description}}",
    "date": "{{event.date}}",
    "time": "{{event.time}}",
    "duration": "{{event.duration_minutes}}",
}
_OLD_RECOMMENDED_PAYLOAD = {
    **_FREE_PAYLOAD,
    "templateId": "{{raid_helper.template_id}}",
    "announcement": "{{rendered.announcement}}",
    "date_variant": "both",
    "12h_format": False,
    "info_variant": "long",
    "preserve_order": True,
    "apply_unregister": True,
}

_LEGACY_ADVANCED_KEYS = set(_OLD_RECOMMENDED_PAYLOAD) - _FREE_KEYS


def _legacy_free_payload(payload: object, template_id: str) -> dict | None:
    if template_id or not isinstance(payload, dict):
        return None
    if set(payload) - set(_OLD_RECOMMENDED_PAYLOAD):
        return None
    for key in _LEGACY_ADVANCED_KEYS & set(payload):
        if payload[key] != _OLD_RECOMMENDED_PAYLOAD[key]:
            return None
    converted = {
        key: payload.get(key, default)
        for key, default in _FREE_PAYLOAD.items()
    }
    return converted


def _dump(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def upgrade() -> None:
    with op.batch_alter_table("raid_helper_templates") as batch:
        batch.add_column(
            sa.Column(
                "uses_premium_features",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )

    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            "SELECT id, raid_template_id, payload_template_json "
            "FROM raid_helper_templates"
        )
    ).mappings()
    for row in rows:
        try:
            payload = json.loads(row["payload_template_json"])
        except (TypeError, json.JSONDecodeError):
            payload = {}
        template_id = (row["raid_template_id"] or "").strip()
        converted_payload = _legacy_free_payload(payload, template_id)
        if converted_payload is not None:
            connection.execute(
                sa.text(
                    "UPDATE raid_helper_templates "
                    "SET payload_template_json = :payload, uses_premium_features = :premium "
                    "WHERE id = :template_id"
                ),
                {
                    "payload": _dump(converted_payload),
                    "premium": False,
                    "template_id": row["id"],
                },
            )
            continue
        has_custom_template = bool(template_id and template_id.lower() != "standard")
        has_advanced_keys = isinstance(payload, dict) and bool(set(payload) - _FREE_KEYS)
        if has_custom_template or has_advanced_keys:
            connection.execute(
                sa.text(
                    "UPDATE raid_helper_templates "
                    "SET uses_premium_features = :premium WHERE id = :template_id"
                ),
                {"premium": True, "template_id": row["id"]},
            )


def downgrade() -> None:
    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            "SELECT id, payload_template_json, uses_premium_features "
            "FROM raid_helper_templates"
        )
    ).mappings()
    for row in rows:
        try:
            payload = json.loads(row["payload_template_json"])
        except (TypeError, json.JSONDecodeError):
            continue
        if not row["uses_premium_features"] and payload == _FREE_PAYLOAD:
            connection.execute(
                sa.text(
                    "UPDATE raid_helper_templates "
                    "SET payload_template_json = :payload WHERE id = :template_id"
                ),
                {"payload": _dump(_OLD_RECOMMENDED_PAYLOAD), "template_id": row["id"]},
            )

    with op.batch_alter_table("raid_helper_templates") as batch:
        batch.drop_column("uses_premium_features")
