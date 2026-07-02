from pydantic import BaseModel

from app.schemas.auth.auth_user import AuthUser


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUser
