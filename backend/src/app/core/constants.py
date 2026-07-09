from __future__ import annotations

from enum import StrEnum


class SiteRole(StrEnum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class FleetRole(StrEnum):
    MEMBER = "member"
    LIEUTENANT = "fleet_lieutenant"
    ADMIRAL = "fleet_admiral"


class MembershipStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"


STAFF_ROLES = {SiteRole.MODERATOR.value, SiteRole.ADMIN.value}
FLEET_LEADERSHIP_ROLES = {FleetRole.ADMIRAL.value, FleetRole.LIEUTENANT.value}
OFFICIAL_FLEET_PROFILE_STATUSES = {MembershipStatus.ACTIVE.value, MembershipStatus.PENDING.value}


FORUM_CATEGORY_GENERAL = "general"
FORUM_CATEGORIES = {
    FORUM_CATEGORY_GENERAL,
    "builds",
    "events",
    "support",
    "training",
    "logistics",
}
FORUM_CATEGORY_ALIASES = {
    "": FORUM_CATEGORY_GENERAL,
    "logistic": "logistics",
    "loistics": "logistics",
}


def normalize_forum_category(value: str | None) -> str:
    normalized = (value or FORUM_CATEGORY_GENERAL).strip().lower().replace(" ", "_").replace("-", "_")
    normalized = FORUM_CATEGORY_ALIASES.get(normalized, normalized)
    return normalized if normalized in FORUM_CATEGORIES else FORUM_CATEGORY_GENERAL
