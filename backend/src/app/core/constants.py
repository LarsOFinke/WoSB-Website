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
