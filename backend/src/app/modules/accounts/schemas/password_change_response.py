from __future__ import annotations


from pydantic import BaseModel

class PasswordChangeResponse(BaseModel):
    changed: bool = True
