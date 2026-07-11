from __future__ import annotations


from pydantic import Field

from app.modules.builds.schemas.build_read import BuildRead
from app.modules.files.schemas.file_asset import FileRead

from app.modules.guides.schemas.guide_summary import GuideSummary

class GuideRead(GuideSummary):
    body: str
    attachments: list[FileRead] = Field(default_factory=list)
    builds: list[BuildRead] = Field(default_factory=list)
