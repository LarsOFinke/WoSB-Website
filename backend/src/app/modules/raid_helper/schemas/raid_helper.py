from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.modules.calendar.constants import FLEET_EVENT_CATEGORY_VALUES

DEFAULT_PAYLOAD_TEMPLATE = '''{
  "title": "{{rendered.title}}",
  "description": "{{rendered.description}}",
  "date": "{{event.date}}",
  "time": "{{event.time}}",
  "duration": "{{event.duration_minutes}}",
  "templateId": "{{raid_helper.template_id}}",
  "announcement": "{{rendered.announcement}}",
  "date_variant": "both",
  "12h_format": false,
  "info_variant": "long",
  "preserve_order": true,
  "apply_unregister": true
}'''


def _categories(values: list[str]) -> list[str]:
    normalized = sorted({value.strip().lower() for value in values if value.strip()})
    invalid = set(normalized) - FLEET_EVENT_CATEGORY_VALUES
    if invalid:
        raise ValueError(f"Invalid event categories: {', '.join(sorted(invalid))}")
    return normalized


class RaidHelperProfileWrite(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    server_id: str = Field(min_length=5, max_length=32, pattern=r"^[0-9]+$")
    api_key: str | None = Field(default=None, max_length=500)
    api_base_url: str = Field(default="https://raid-helper.xyz/api/v4", max_length=200)
    authorization_mode: Literal["authorization", "bearer", "x-api-key"] = "authorization"
    timezone: str = Field(default="Europe/Berlin", min_length=1, max_length=80)
    default_leader_id: str | None = Field(default=None, min_length=5, max_length=32, pattern=r"^[0-9]+$")
    is_active: bool = True

    @model_validator(mode="after")
    def normalize(self):
        self.name = self.name.strip()
        self.server_id = self.server_id.strip()
        self.api_base_url = self.api_base_url.strip().rstrip("/")
        self.timezone = self.timezone.strip()
        if isinstance(self.default_leader_id, str):
            self.default_leader_id = self.default_leader_id.strip() or None
        if isinstance(self.api_key, str):
            self.api_key = self.api_key.strip() or None
        return self


class RaidHelperProfileCreate(RaidHelperProfileWrite):
    api_key: str = Field(min_length=8, max_length=500)


class RaidHelperProfileRead(BaseModel):
    id: int
    name: str
    server_id: str
    api_base_url: str
    authorization_mode: str
    timezone: str
    default_leader_id: str | None = None
    is_active: bool
    api_key_configured: bool
    created_by_username: str
    created_at: datetime
    updated_at: datetime


class RaidHelperDestinationWrite(BaseModel):
    profile_id: int
    name: str = Field(min_length=1, max_length=120)
    channel_id: str = Field(min_length=5, max_length=32, pattern=r"^[0-9]+$")
    scope_type: Literal["fleet", "squad"]
    squad_id: int | None = None
    categories: list[str] = Field(default_factory=list)
    is_default: bool = False
    is_active: bool = True

    @model_validator(mode="after")
    def normalize(self):
        self.name = self.name.strip()
        self.channel_id = self.channel_id.strip()
        self.categories = _categories(self.categories)
        if self.scope_type == "fleet" and self.squad_id is not None:
            raise ValueError("Fleet destinations cannot reference a squad.")
        if self.scope_type == "squad" and self.squad_id is None:
            raise ValueError("Squad destinations require a squad.")
        return self


class RaidHelperDestinationRead(RaidHelperDestinationWrite):
    id: int
    profile_name: str
    squad_name: str | None = None
    created_at: datetime
    updated_at: datetime


class RaidHelperTemplateWrite(BaseModel):
    profile_id: int
    name: str = Field(min_length=1, max_length=120)
    raid_template_id: str = Field(default="Standard", min_length=1, max_length=80)
    scope_type: Literal["both", "fleet", "squad"] = "both"
    categories: list[str] = Field(default_factory=list)
    title_template: str = Field(default="{{event.title}}", min_length=1, max_length=300)
    description_template: str = Field(default="{{event.description}}", max_length=4000)
    announcement_template: str = Field(default="", max_length=2000)
    payload_template_json: str = Field(default=DEFAULT_PAYLOAD_TEMPLATE, min_length=2, max_length=12000)
    is_default: bool = False
    is_active: bool = True

    @model_validator(mode="after")
    def normalize(self):
        import json
        self.name = self.name.strip()
        self.raid_template_id = self.raid_template_id.strip()
        self.categories = _categories(self.categories)
        self.title_template = self.title_template.strip()
        self.description_template = self.description_template.strip()
        self.announcement_template = self.announcement_template.strip()
        try:
            value = json.loads(self.payload_template_json)
        except json.JSONDecodeError as exc:
            raise ValueError("Payload template must contain valid JSON.") from exc
        if not isinstance(value, dict):
            raise ValueError("Payload template must be a JSON object.")
        self.payload_template_json = json.dumps(value, ensure_ascii=False, indent=2)
        return self


class RaidHelperTemplateRead(RaidHelperTemplateWrite):
    id: int
    profile_name: str
    created_at: datetime
    updated_at: datetime


class RaidHelperDispatchSelection(BaseModel):
    destination_id: int
    template_id: int
    leader_id: str | None = Field(default=None, min_length=5, max_length=32, pattern=r"^[0-9]+$")

    @model_validator(mode="after")
    def normalize(self):
        if isinstance(self.leader_id, str):
            self.leader_id = self.leader_id.strip() or None
        return self


class RaidHelperOptionTemplate(BaseModel):
    id: int
    name: str
    profile_id: int
    profile_name: str
    raid_template_id: str
    is_default: bool


class RaidHelperOptionDestination(BaseModel):
    id: int
    name: str
    profile_id: int
    profile_name: str
    scope_type: str
    squad_id: int | None = None
    is_default: bool
    default_leader_id: str | None = None
    templates: list[RaidHelperOptionTemplate]


class RaidHelperEventLinkRead(BaseModel):
    id: int
    destination_id: int
    destination_name: str
    template_id: int
    template_name: str
    external_event_id: str | None = None
    status: str
    last_operation: str
    error_message: str | None = None
    synced_at: datetime | None = None


class RaidHelperProfileTestResult(BaseModel):
    ok: bool
    status_code: int | None = None
    message: str
