from __future__ import annotations

from typing import Any


def forum_and_fleet_samples(
    common_event: dict[str, Any], common_user: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    return {
        "forum.thread.removed": {
            **common_event,
            "resource_type": "forum_thread",
            "resource_id": 501,
            "resource_url": "/forum",
            "data": {"id": 501, "title": "Fleet formation questions"},
        },
        "forum.post.created": {
            **common_event,
            "resource_type": "forum_post",
            "resource_id": 502,
            "resource_url": "/forum/501",
            "data": {
                "id": 502,
                "thread_id": 501,
                "author": common_user,
                "body": "Formation reply",
                "created_at": "2026-08-16T12:00:00+00:00",
            },
        },
        "forum.post.updated": {
            **common_event,
            "resource_type": "forum_post",
            "resource_id": 502,
            "resource_url": "/forum/501",
            "data": {
                "id": 502,
                "thread_id": 501,
                "author": common_user,
                "body": "Updated formation reply",
                "updated_at": "2026-08-16T13:00:00+00:00",
            },
        },
        "forum.post.removed": {
            **common_event,
            "resource_type": "forum_post",
            "resource_id": 502,
            "resource_url": "/forum/501",
            "data": {"id": 502, "thread_id": 501, "author": common_user},
        },
        "fleet.created": {
            **common_event,
            "resource_type": "fleet",
            "resource_id": 1,
            "resource_url": "/fleet",
            "data": {
                "id": 1,
                "name": "Royal Blackwater Fleet",
                "focus": "mixed",
                "description": "Official fleet",
                "active_members_count": 1,
            },
        },
        "fleet.updated": {
            **common_event,
            "resource_type": "fleet",
            "resource_id": 1,
            "resource_url": "/fleet",
            "data": {
                "id": 1,
                "name": "Royal Blackwater Fleet",
                "focus": "mixed",
                "description": "Updated official fleet",
                "active_members_count": 12,
            },
        },
        "fleet.application.created": {
            **common_event,
            "resource_type": "fleet_membership",
            "resource_id": 701,
            "resource_url": "/fleets",
            "data": {
                "id": 701,
                "fleet_id": 1,
                "user": common_user,
                "status": "pending",
                "note": "Ready to sail",
            },
        },
        "fleet.membership.updated": {
            **common_event,
            "resource_type": "fleet_membership",
            "resource_id": 701,
            "resource_url": "/fleets",
            "data": {
                "id": 701,
                "fleet_id": 1,
                "user": common_user,
                "status": "active",
                "role": "member",
                "assignment": "Line squadron",
            },
        },
        "fleet.leader.assigned": {
            **common_event,
            "resource_type": "fleet_membership",
            "resource_id": 702,
            "resource_url": "/fleets",
            "data": {
                "id": 702,
                "fleet_id": 1,
                "user": common_user,
                "status": "active",
                "role": "fleet_admiral",
                "assignment": "Fleet command",
            },
        },
        "fleet.role.created": {
            **common_event,
            "resource_type": "fleet_role",
            "resource_id": 801,
            "resource_url": "/fleets",
            "data": {
                "id": 801,
                "code": "quartermaster",
                "label": "Quartermaster",
                "rank": 20,
                "is_active": True,
            },
        },
        "fleet.role.updated": {
            **common_event,
            "resource_type": "fleet_role",
            "resource_id": 801,
            "resource_url": "/fleets",
            "data": {
                "id": 801,
                "code": "quartermaster",
                "label": "Senior Quartermaster",
                "rank": 22,
                "is_active": True,
            },
        },
        "fleet.role.removed": {
            **common_event,
            "resource_type": "fleet_role",
            "resource_id": 801,
            "resource_url": "/fleets",
            "data": {"id": 801, "code": "quartermaster", "label": "Quartermaster"},
        },
    }


__all__ = ["forum_and_fleet_samples"]
