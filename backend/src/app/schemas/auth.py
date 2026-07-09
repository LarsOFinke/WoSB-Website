from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

USER_ROLE_VALUES = {"user", "moderator", "admin"}
PREFERRED_FOCUS_VALUES = {
    "pve_farming",
    "pve_imp_hunting",
    "pve_general",
    "pvp_open_world",
    "pvp_arena",
    "pvp_general",
    "trading",
    "other",
}


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=6, max_length=200)
    display_name: str = Field(min_length=1, max_length=120)
    fleet_name: str | None = Field(default=None, max_length=120)
    fleet_id: int | None = None
    wants_fleet_membership: bool = False
    fleet_application_note: str | None = Field(default=None, max_length=1000)
    fleet_availability: str | None = Field(default=None, max_length=240)
    fleet_preferred_ships: str | None = Field(default=None, max_length=300)
    fleet_timezone: str | None = Field(default=None, max_length=80)
    fleet_discord_handle: str | None = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def normalize(self) -> "RegisterRequest":
        self.username = self.username.strip().lower()
        self.display_name = self.display_name.strip()
        if isinstance(self.fleet_name, str):
            self.fleet_name = self.fleet_name.strip() or None
        for field_name in ["fleet_application_note", "fleet_availability", "fleet_preferred_ships", "fleet_timezone", "fleet_discord_handle"]:
            value = getattr(self, field_name)
            if isinstance(value, str):
                setattr(self, field_name, value.strip() or None)
        if self.fleet_id is not None:
            self.wants_fleet_membership = True
        return self


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str
    role: str
    is_active: bool
    fleet_name: str | None = None
    fleet_id: int | None = None
    fleet_membership_id: int | None = None
    fleet_membership_status: str | None = None
    fleet_membership_role: str | None = None
    preferred_focus: str | None = None
    note: str | None = None
    created_at: datetime


class LoginResponse(BaseModel):
    user: UserRead


class RegistrationRequestPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str
    status: str
    created_at: datetime


class RegisterResponse(BaseModel):
    request: RegistrationRequestPublic
    message: str = "Registration request submitted for admin review."


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=6, max_length=200)

    @model_validator(mode="after")
    def validate_new_password(self) -> "PasswordChangeRequest":
        if self.current_password == self.new_password:
            raise ValueError("New password must be different from the current password.")
        return self


class PasswordChangeResponse(BaseModel):
    changed: bool = True


class ProfileUpdate(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    fleet_name: str | None = Field(default=None, max_length=120)
    fleet_id: int | None = None
    preferred_focus: str | None = Field(default=None, max_length=80)
    note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def normalize(self) -> "ProfileUpdate":
        self.display_name = self.display_name.strip()
        if isinstance(self.fleet_name, str):
            self.fleet_name = self.fleet_name.strip() or None
        if isinstance(self.preferred_focus, str):
            self.preferred_focus = self.preferred_focus.strip() or None
            if self.preferred_focus and self.preferred_focus not in PREFERRED_FOCUS_VALUES:
                raise ValueError("Invalid preferred focus.")
        if isinstance(self.note, str):
            self.note = self.note.strip() or None
        return self
