"""Canonicalize Raid-Helper API host and safe payload defaults.

Revision ID: 0016_raid_helper_api_host
Revises: 0015_bootstrap_admin_files
"""

from __future__ import annotations

import json

from alembic import op
import sqlalchemy as sa

revision: str = "0016_raid_helper_api_host"
down_revision: str = "0015_bootstrap_admin_files"
branch_labels = None
depends_on = None

_OLD_DEFAULT_PAYLOAD = {
    "title": "{{rendered.title}}",
    "description": "{{rendered.description}}",
    "date": "{{event.date}}",
    "time": "{{event.time}}",
    "duration": "{{event.duration_minutes}}",
    "templateId": "{{raid_helper.template_id}}",
    "announcement": "{{rendered.announcement}}",
}
_RECOMMENDED_DEFAULT_PAYLOAD = {
    **_OLD_DEFAULT_PAYLOAD,
    "date_variant": "both",
    "12h_format": False,
    "info_variant": "long",
    "preserve_order": True,
    "apply_unregister": True,
}


def _replace_exact_default(source: dict[str, object], target: dict[str, object]) -> None:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text("SELECT id, payload_template_json FROM raid_helper_templates")
    ).mappings()
    for row in rows:
        try:
            payload = json.loads(row["payload_template_json"])
        except (TypeError, json.JSONDecodeError):
            continue
        if payload != source:
            continue
        bind.execute(
            sa.text(
                "UPDATE raid_helper_templates "
                "SET payload_template_json = :payload WHERE id = :template_id"
            ),
            {
                "payload": json.dumps(target, ensure_ascii=False, indent=2),
                "template_id": row["id"],
            },
        )


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE raid_helper_profiles
            SET api_base_url = 'https://raid-helper.xyz/api/v4'
            WHERE api_base_url IN (
                'https://raid-helper.dev/api/v4',
                'https://www.raid-helper.dev/api/v4',
                'https://www.raid-helper.xyz/api/v4'
            )
            """
        )
    )
    _replace_exact_default(_OLD_DEFAULT_PAYLOAD, _RECOMMENDED_DEFAULT_PAYLOAD)


def downgrade() -> None:
    _replace_exact_default(_RECOMMENDED_DEFAULT_PAYLOAD, _OLD_DEFAULT_PAYLOAD)
    op.execute(
        sa.text(
            """
            UPDATE raid_helper_profiles
            SET api_base_url = 'https://raid-helper.dev/api/v4'
            WHERE api_base_url = 'https://raid-helper.xyz/api/v4'
            """
        )
    )
