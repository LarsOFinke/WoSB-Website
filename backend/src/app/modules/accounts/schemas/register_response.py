from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.accounts.schemas.registration_request_public import RegistrationRequestPublic

class RegisterResponse(BaseModel):
    request: RegistrationRequestPublic
    message: str = "Registration request submitted for admin review."
