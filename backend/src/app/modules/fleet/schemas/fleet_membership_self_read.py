from __future__ import annotations



from app.modules.fleet.schemas.fleet_membership_read import FleetMembershipRead
from app.modules.fleet.schemas.fleet_membership_fleet_read import FleetMembershipFleetRead

class FleetMembershipSelfRead(FleetMembershipRead):
    fleet: FleetMembershipFleetRead
