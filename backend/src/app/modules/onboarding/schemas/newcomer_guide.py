from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

BlockType = Literal["text", "resources"]
ResourceType = Literal["guide", "build", "internal", "external"]


class NewcomerGuideResourceInput(BaseModel):
    resource_type: ResourceType
    resource_id: int | None = None
    label: str | None = Field(default=None, max_length=180)
    description: str | None = Field(default=None, max_length=500)
    url: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def normalize(self) -> "NewcomerGuideResourceInput":
        self.label = self.label.strip() or None if isinstance(self.label, str) else None
        self.description = self.description.strip() or None if isinstance(self.description, str) else None
        self.url = self.url.strip() or None if isinstance(self.url, str) else None
        if self.resource_type in {"guide", "build"}:
            if not self.resource_id or self.resource_id <= 0:
                raise ValueError("Guide and build links require a valid resource id.")
            self.url = None
        elif not self.url:
            raise ValueError("Internal and external links require a URL.")
        return self


class NewcomerGuideBlockInput(BaseModel):
    block_type: BlockType
    title: str = Field(min_length=1, max_length=180)
    body: str | None = Field(default=None, max_length=20000)
    resources: list[NewcomerGuideResourceInput] = Field(default_factory=list, max_length=30)

    @model_validator(mode="after")
    def normalize(self) -> "NewcomerGuideBlockInput":
        self.title = self.title.strip()
        self.body = self.body.strip() or None if isinstance(self.body, str) else None
        if self.block_type == "text":
            self.resources = []
            if not self.body:
                raise ValueError("Text blocks require body content.")
        return self


class NewcomerGuideUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    intro: str = Field(default="", max_length=4000)
    blocks: list[NewcomerGuideBlockInput] = Field(default_factory=list, max_length=30)

    @model_validator(mode="after")
    def normalize(self) -> "NewcomerGuideUpdate":
        self.title = self.title.strip()
        self.intro = self.intro.strip()
        return self


class NewcomerGuideResourceRead(BaseModel):
    id: int
    resource_type: ResourceType
    resource_id: int | None = None
    label: str
    description: str | None = None
    href: str
    available: bool = True


class NewcomerGuideBlockRead(BaseModel):
    id: int
    block_type: BlockType
    title: str
    body: str | None = None
    resources: list[NewcomerGuideResourceRead] = Field(default_factory=list)


class NewcomerGuideRead(BaseModel):
    id: int
    title: str
    intro: str
    blocks: list[NewcomerGuideBlockRead] = Field(default_factory=list)
    updated_at: datetime
    updated_by: str | None = None
