from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class LegalNoticeFields(BaseModel):
    model_config = ConfigDict(extra="forbid")

    published: bool = False
    provider_name: str = Field(default="", max_length=200)
    legal_form: str = Field(default="", max_length=120)
    represented_by: str = Field(default="", max_length=300)
    street: str = Field(default="", max_length=200)
    postal_code: str = Field(default="", max_length=32)
    city: str = Field(default="", max_length=120)
    country: str = Field(default="Deutschland", max_length=120)
    email: str = Field(default="", max_length=254)
    phone: str = Field(default="", max_length=80)
    register_name: str = Field(default="", max_length=160)
    register_court: str = Field(default="", max_length=200)
    register_number: str = Field(default="", max_length=120)
    vat_id: str = Field(default="", max_length=80)
    business_id: str = Field(default="", max_length=120)
    supervisory_authority: str = Field(default="", max_length=500)
    editorial_responsible_name: str = Field(default="", max_length=200)
    editorial_responsible_street: str = Field(default="", max_length=200)
    editorial_responsible_postal_code: str = Field(default="", max_length=32)
    editorial_responsible_city: str = Field(default="", max_length=120)
    editorial_responsible_country: str = Field(default="Deutschland", max_length=120)
    dispute_resolution_text: str = Field(default="", max_length=4000)
    additional_information: str = Field(default="", max_length=4000)

    @field_validator("*")
    @classmethod
    def strip_strings(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if value and ("@" not in value or value.startswith("@") or value.endswith("@")):
            raise ValueError("Enter a valid contact email address.")
        return value

    @model_validator(mode="after")
    def validate_publishable_document(self) -> "LegalNoticeFields":
        if not self.published:
            return self
        required = {
            "provider_name": self.provider_name,
            "street": self.street,
            "postal_code": self.postal_code,
            "city": self.city,
            "country": self.country,
            "email": self.email,
        }
        missing = [field for field, value in required.items() if not value]
        if missing:
            raise ValueError(
                "A published legal notice requires provider name, complete address and email. "
                f"Missing: {', '.join(missing)}."
            )
        editorial = [
            self.editorial_responsible_name,
            self.editorial_responsible_street,
            self.editorial_responsible_postal_code,
            self.editorial_responsible_city,
        ]
        if any(editorial) and not all(editorial):
            raise ValueError(
                "Editorial responsibility requires name and a complete postal address."
            )
        return self


class LegalNoticeUpdate(LegalNoticeFields):
    pass


class LegalNoticeAdminRead(LegalNoticeFields):
    model_config = ConfigDict(from_attributes=True)

    source: str
    updated_by_username: str
    updated_at: datetime


class LegalNoticePublicRead(LegalNoticeFields):
    model_config = ConfigDict(from_attributes=True)

    updated_at: datetime | None = None
