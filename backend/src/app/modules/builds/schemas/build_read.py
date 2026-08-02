from __future__ import annotations

from datetime import datetime

from pydantic import ConfigDict

from app.modules.ships.schemas.ship import ShipRead

from app.modules.builds.schemas.ship_stats import ShipStats
from app.modules.builds.schemas.build_base import BuildBase

class BuildRead(BuildBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int | None = None
    is_official_template: bool = False
    build_role_label: str
    upvote_count: int = 0
    has_upvoted: bool = False
    ship: ShipRead
    ship_stats: ShipStats
    created_at: datetime
    updated_at: datetime
    printout_url: str | None = None
    printout_checksum: str | None = None
