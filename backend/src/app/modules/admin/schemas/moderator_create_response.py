from __future__ import annotations


from pydantic import BaseModel

from app.modules.accounts.schemas.user_read import UserRead

class ModeratorCreateResponse(BaseModel):
    user: UserRead
