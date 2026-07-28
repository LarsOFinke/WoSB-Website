from pydantic import BaseModel, Field


class AppLogDeleteResult(BaseModel):
    deleted_count: int = Field(ge=0)
