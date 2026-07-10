from __future__ import annotations

from app.core.fleet_role import FleetRole
from app.core.membership_status import MembershipStatus
from app.core.site_role import SiteRole

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


__all__ = [
    "SiteRole",
    "FleetRole",
    "MembershipStatus",
    "STAFF_ROLES",
    "FLEET_LEADERSHIP_ROLES",
    "OFFICIAL_FLEET_PROFILE_STATUSES",
    "FORUM_CATEGORY_GENERAL",
    "FORUM_CATEGORIES",
    "FORUM_CATEGORY_ALIASES",
    "normalize_forum_category",
]
