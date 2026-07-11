from __future__ import annotations


from pydantic import Field



from app.modules.forum.schemas.forum_post_read import ForumPostRead
from app.modules.forum.schemas.forum_thread_summary import ForumThreadSummary

class ForumThreadRead(ForumThreadSummary):
    posts: list[ForumPostRead] = Field(default_factory=list)
