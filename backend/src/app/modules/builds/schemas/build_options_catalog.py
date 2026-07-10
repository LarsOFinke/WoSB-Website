from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.builds.schemas.build_item_category_read import BuildItemCategoryRead
from app.modules.builds.schemas.build_item_option_read import BuildItemOptionRead
from app.modules.builds.schemas.build_stat_definition_read import BuildStatDefinitionRead

class BuildOptionsCatalog(BaseModel):
    categories: list[BuildItemCategoryRead]
    options: dict[str, list[BuildItemOptionRead]]
    stat_definitions: list[BuildStatDefinitionRead] = Field(default_factory=list)
