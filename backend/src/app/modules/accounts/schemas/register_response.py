from __future__ import annotations


from pydantic import BaseModel

from app.modules.accounts.schemas.registration_request_public import RegistrationRequestPublic

class RegisterResponse(BaseModel):
    request: RegistrationRequestPublic
    message: str = "Registration request submitted for admin review."
