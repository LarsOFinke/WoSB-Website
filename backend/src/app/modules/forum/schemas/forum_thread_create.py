from __future__ import annotations


from pydantic import Field, model_validator

from app.core.constants import normalize_forum_category


from app.modules.forum.schemas.forum_post_create import ForumPostCreate

class ForumThreadCreate(ForumPostCreate):
    title: str = Field(min_length=1, max_length=160)
    category: str = Field(default="general", max_length=80)

    @model_validator(mode="after")
    def normalize_thread(self) -> "ForumThreadCreate":
        self.title = self.title.strip()
        self.category = normalize_forum_category(self.category)
        return self
