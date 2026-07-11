from __future__ import annotations



from app.modules.fleet.schemas.fleet_membership_read import FleetMembershipRead
from app.modules.fleet.schemas.fleet_read import FleetRead

class FleetDetail(FleetRead):
    memberships: list[FleetMembershipRead] = []
