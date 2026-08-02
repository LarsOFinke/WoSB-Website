from __future__ import annotations

from typing import Any


def build_samples(common_event: dict[str, Any]) -> dict[str, dict[str, Any]]:
    build_data = {
        "id": 401,
        "build_name": "Heavy Broadside",
        "build_type": "balanced",
        "ship": {"id": 12, "name": "Anson", "rate": 3},
        "is_official_template": False,
        "sailors": 80,
        "soldiers": 80,
        "musketeers": 0,
        "mercenaries": 0,
        "owner_id": 42,
        "created_at": "2026-08-15T12:00:00+00:00",
        "updated_at": "2026-08-15T12:00:00+00:00",
    }
    updated_data = {
        **build_data,
        "build_name": "Heavy Broadside Mk II",
        "sailors": 90,
        "soldiers": 70,
        "updated_at": "2026-08-16T12:00:00+00:00",
    }
    return {
        "build.created": {
            **common_event,
            "resource_type": "build",
            "resource_id": 401,
            "resource_url": "/builds/401",
            "data": build_data,
        },
        "build.updated": {
            **common_event,
            "resource_type": "build",
            "resource_id": 401,
            "resource_url": "/builds/401",
            "data": updated_data,
        },
        "build.printout.published": {
            **common_event,
            "resource_type": "build_printout",
            "resource_id": 401,
            "resource_url": "/api/builds/401/printout",
            "data": {
                "id": 401,
                "build_name": "Heavy Broadside Mk II",
                "build_url": "/builds/401",
                "image_url": "/api/builds/401/printout",
                "checksum": "0" * 64,
                "changed": True,
            },
        },
        "build.removed": {
            **common_event,
            "resource_type": "build",
            "resource_id": 401,
            "resource_url": "/builds",
            "data": {"id": 401, "build_name": "Heavy Broadside Mk II"},
        },
    }
