from datetime import date

from sqlalchemy import CheckConstraint, Date, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utc_now
from app.db.base import Base


SECURITY_SIGNAL_RECONNAISSANCE = "reconnaissance"
SECURITY_SIGNAL_LOGIN_FAILURE = "login_failure"
SECURITY_SIGNAL_RATE_LIMIT = "rate_limit"
SECURITY_REASON_LOGIN_REJECTED = "login_rejected"
SECURITY_REASON_RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
SECURITY_REASON_SUSPICIOUS_PROBE = "suspicious_probe"
SECURITY_REASON_LEGACY_AGGREGATE = "legacy_aggregate"
SECURITY_SIGNALS = frozenset(
    {
        SECURITY_SIGNAL_RECONNAISSANCE,
        SECURITY_SIGNAL_LOGIN_FAILURE,
        SECURITY_SIGNAL_RATE_LIMIT,
    }
)


class SecuritySignalBucket(Base):
    """Daily, purpose-bound signal counts used only for IP-ban decisions.

    Individual request timestamps are intentionally not retained. At most one
    row per IP, signal, reason, target and UTC day exists.
    """

    __tablename__ = "security_signal_buckets"
    __table_args__ = (
        CheckConstraint(
            "signal IN ('reconnaissance', 'login_failure', 'rate_limit')",
            name="ck_security_signal_buckets_signal",
        ),
        CheckConstraint("event_count >= 1", name="ck_security_signal_buckets_count"),
        UniqueConstraint(
            "day",
            "client_ip",
            "signal",
            "reason",
            "request_target",
            name="uq_security_signal_buckets_dimensions",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    day: Mapped[date] = mapped_column(Date, nullable=False, default=lambda: utc_now().date(), index=True)
    client_ip: Mapped[str] = mapped_column(String(45), nullable=False, index=True)
    signal: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(
        String(32), nullable=False, default=SECURITY_REASON_LEGACY_AGGREGATE
    )
    request_target: Mapped[str] = mapped_column(
        String(180), nullable=False, default="unknown"
    )
    event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


# Compatibility alias for internal imports while callers migrate to the more
# accurate bucket terminology.
SecurityEvent = SecuritySignalBucket
