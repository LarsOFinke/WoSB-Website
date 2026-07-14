from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utc_now
from app.db.base import Base


class OutboundWebhook(Base):
    """Admin-managed outbound webhook subscription for external integrations."""

    __tablename__ = "outbound_webhooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    endpoint_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    signing_secret: Mapped[str] = mapped_column(String(160), nullable=False)
    event_types_json: Mapped[str] = mapped_column(Text, nullable=False)
    channel_key: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    message_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now, onupdate=utc_now, index=True)
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_by_username: Mapped[str] = mapped_column(String(80), nullable=False)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_by: Mapped["User | None"] = relationship("User", lazy="joined")
    deliveries: Mapped[list["OutboundWebhookDelivery"]] = relationship(
        "OutboundWebhookDelivery",
        back_populates="webhook",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class OutboundWebhookDelivery(Base):
    """Persisted delivery attempt history for outbound webhook events."""

    __tablename__ = "outbound_webhook_deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    webhook_id: Mapped[int] = mapped_column(
        ForeignKey("outbound_webhooks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    delivery_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="queued", index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now, index=True)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)

    webhook: Mapped[OutboundWebhook] = relationship("OutboundWebhook", back_populates="deliveries", lazy="joined")
