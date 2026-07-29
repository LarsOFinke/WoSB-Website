from pydantic import BaseModel, Field


class BuildVoteState(BaseModel):
    build_id: int
    upvote_count: int = Field(ge=0)
    has_upvoted: bool
