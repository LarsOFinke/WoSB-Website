from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

class PasswordChangeResponse(BaseModel):
    changed: bool = True
