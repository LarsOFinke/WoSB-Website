from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AppLog(Base):
    """Persisted application/request log entry for the admin dashboard."""

    __tablename__ = "app_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    logger: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    method: Mapped[str | None] = mapped_column(String(12), nullable=True, index=True)
    path: Mapped[str | None] = mapped_column(String(300), nullable=True, index=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    client: Mapped[str | None] = mapped_column(String(120), nullable=True)
    exception: Mapped[str | None] = mapped_column(Text, nullable=True)
