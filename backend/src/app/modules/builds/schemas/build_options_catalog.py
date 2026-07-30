from __future__ import annotations


from pydantic import BaseModel, Field

from app.modules.builds.schemas.build_item_category_read import BuildItemCategoryRead
from app.modules.builds.schemas.build_role import BuildRoleRead
from app.modules.builds.schemas.build_item_option_read import BuildItemOptionRead
from app.modules.builds.schemas.build_stat_definition_read import BuildStatDefinitionRead

class BuildOptionsCatalog(BaseModel):
    build_roles: list[BuildRoleRead] = Field(default_factory=list)
    categories: list[BuildItemCategoryRead]
    options: dict[str, list[BuildItemOptionRead]]
    stat_definitions: list[BuildStatDefinitionRead] = Field(default_factory=list)
    research_upgrade_slot_effects: dict[str, int | float] = Field(default_factory=dict)
    research_upgrade_slot_grant: int = Field(default=0, ge=0, le=8)
    limits: dict[str, int] = Field(default_factory=dict)
