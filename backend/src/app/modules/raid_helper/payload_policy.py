from __future__ import annotations

import json
from typing import Any


FREE_PAYLOAD_KEYS = frozenset({
    "title",
    "description",
    "date",
    "time",
    "duration",
    "leaderId",
})

FREE_PAYLOAD_TEMPLATE = '''{
  "title": "{{rendered.title}}",
  "description": "{{rendered.description}}",
  "date": "{{event.date}}",
  "time": "{{event.time}}",
  "duration": "{{event.duration_minutes}}"
}'''

PREMIUM_PAYLOAD_TEMPLATE = '''{
  "title": "{{rendered.title}}",
  "description": "{{rendered.description}}",
  "date": "{{event.date}}",
  "time": "{{event.time}}",
  "duration": "{{event.duration_minutes}}",
  "templateId": "{{raid_helper.template_id}}",
  "announcement": "{{rendered.announcement}}",
  "date_variant": "both",
  "12h_format": false,
  "info_variant": "long",
  "preserve_order": true,
  "apply_unregister": true
}'''


def payload_object(payload_template_json: str) -> dict[str, Any]:
    try:
        value = json.loads(payload_template_json)
    except json.JSONDecodeError as exc:
        raise ValueError("Raid-Helper payload template must contain valid JSON.") from exc
    if not isinstance(value, dict):
        raise ValueError("Raid-Helper payload template must be a JSON object.")
    return value


def premium_reasons(*, raid_template_id: str, payload_template_json: str) -> list[str]:
    reasons: list[str] = []
    normalized_template_id = raid_template_id.strip()
    if normalized_template_id and normalized_template_id.lower() != "standard":
        reasons.append("custom templateId")
    payload = payload_object(payload_template_json)
    extra_keys_set = set(payload) - FREE_PAYLOAD_KEYS
    if not normalized_template_id or normalized_template_id.lower() == "standard":
        extra_keys_set.discard("templateId")
    extra_keys = sorted(extra_keys_set)
    if extra_keys:
        reasons.append(f"advanced kwargs: {', '.join(extra_keys)}")
    return reasons


def validate_payload_capability(
    *,
    raid_template_id: str,
    payload_template_json: str,
    uses_premium_features: bool,
) -> None:
    payload = payload_object(payload_template_json)
    if not uses_premium_features:
        missing = sorted({"title", "date", "time"} - set(payload))
        if missing:
            raise ValueError(
                "A free-compatible Raid-Helper payload must include: "
                + ", ".join(missing)
                + "."
            )
    reasons = premium_reasons(
        raid_template_id=raid_template_id,
        payload_template_json=payload_template_json,
    )
    if reasons and not uses_premium_features:
        raise ValueError(
            "This Raid-Helper template is outside the free-compatible payload ("
            + "; ".join(reasons)
            + "). Enable Premium/custom features only for a server that supports them, "
            "or apply the free-compatible payload preset."
        )
