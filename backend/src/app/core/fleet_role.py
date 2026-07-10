from __future__ import annotations

from enum import StrEnum


class FleetRole(StrEnum):
    MEMBER = "member"
    LIEUTENANT = "fleet_lieutenant"
    ADMIRAL = "fleet_admiral"
