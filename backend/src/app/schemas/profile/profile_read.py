from pydantic import BaseModel


class ProfileRead(BaseModel):
    user_id: int
    display_name: str
    main_role: str
    fleet: str
    bio: str
    preferred_ship_id: int | None = None
    preferred_ship_name: str | None = None
