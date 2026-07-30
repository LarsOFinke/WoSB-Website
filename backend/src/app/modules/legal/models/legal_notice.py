from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utc_now
from app.db.base import Base


class LegalNotice(Base):
    """Singleton provider-information document shown on the public legal page."""

    __tablename__ = "legal_notices"
    __table_args__ = (CheckConstraint("id = 1", name="ck_legal_notice_singleton"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_customized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    provider_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    legal_form: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    represented_by: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    street: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    postal_code: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    city: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    country: Mapped[str] = mapped_column(String(120), nullable=False, default="Deutschland")
    email: Mapped[str] = mapped_column(String(254), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(80), nullable=False, default="")

    register_name: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    register_court: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    register_number: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    vat_id: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    business_id: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    supervisory_authority: Mapped[str] = mapped_column(String(500), nullable=False, default="")

    editorial_responsible_name: Mapped[str] = mapped_column(
        String(200), nullable=False, default=""
    )
    editorial_responsible_street: Mapped[str] = mapped_column(
        String(200), nullable=False, default=""
    )
    editorial_responsible_postal_code: Mapped[str] = mapped_column(
        String(32), nullable=False, default=""
    )
    editorial_responsible_city: Mapped[str] = mapped_column(
        String(120), nullable=False, default=""
    )
    editorial_responsible_country: Mapped[str] = mapped_column(
        String(120), nullable=False, default="Deutschland"
    )

    dispute_resolution_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    additional_information: Mapped[str] = mapped_column(Text, nullable=False, default="")
    updated_by_username: Mapped[str] = mapped_column(String(80), nullable=False, default="environment")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )
