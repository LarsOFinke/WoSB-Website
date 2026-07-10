from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.constants import normalize_forum_category

from app.modules.accounts.schemas.user_read import UserRead
from app.modules.files.schemas.file_asset import FileRead

from app.modules.forum.schemas.forum_post_read import ForumPostRead
from app.modules.forum.schemas.forum_thread_summary import ForumThreadSummary

class ForumThreadRead(ForumThreadSummary):
    posts: list[ForumPostRead] = Field(default_factory=list)
