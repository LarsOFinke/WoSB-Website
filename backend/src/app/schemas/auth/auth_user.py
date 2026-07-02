from pydantic import BaseModel


class AuthUser(BaseModel):
    id: int
    username: str
    display_name: str
    role: str
    is_admin: bool = False
