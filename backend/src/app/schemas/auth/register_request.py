from pydantic import Field

from app.schemas.auth.login_request import LoginRequest


class RegisterRequest(LoginRequest):
    display_name: str | None = Field(default=None, max_length=80)
