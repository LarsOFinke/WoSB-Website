from __future__ import annotations

import logging
from ipaddress import IPv6Address, ip_address

from sqlalchemy import select

from app.core.time import utc_now


class SecurityEventHandler(logging.Handler):
    """Aggregate only explicit, purpose-bound IP-ban signals.

    Messages, raw paths, query strings, user agents, request IDs, exceptions
    and exact request timestamps are ignored. Known route templates and fixed
    probe categories are retained only as daily aggregate dimensions.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            from app.db.session import SessionLocal
            from app.modules.admin.models.security_event import (
                SECURITY_SIGNALS,
                SECURITY_REASON_LEGACY_AGGREGATE,
                SecuritySignalBucket,
            )

            signal = str(getattr(record, "security_signal", "")).strip()
            raw_ip = str(getattr(record, "client_ip", "")).strip()
            reason = str(
                getattr(record, "security_reason", SECURITY_REASON_LEGACY_AGGREGATE)
            ).strip()[:32]
            request_target = str(
                getattr(record, "security_request_target", "unknown")
            ).strip()[:180]
            if signal not in SECURITY_SIGNALS or not raw_ip:
                return
            if not reason or not request_target:
                return

            parsed = ip_address(raw_ip)
            if isinstance(parsed, IPv6Address) and parsed.ipv4_mapped:
                parsed = parsed.ipv4_mapped

            now = utc_now()
            values = {
                "day": now.date(),
                "client_ip": parsed.compressed,
                "signal": signal,
                "reason": reason,
                "request_target": request_target,
                "event_count": 1,
            }
            with SessionLocal() as db:
                dialect = db.get_bind().dialect.name
                if dialect == "postgresql":
                    from sqlalchemy.dialects.postgresql import insert

                    statement = insert(SecuritySignalBucket).values(**values)
                    statement = statement.on_conflict_do_update(
                        constraint="uq_security_signal_buckets_dimensions",
                        set_={"event_count": SecuritySignalBucket.event_count + 1},
                    )
                    db.execute(statement)
                elif dialect == "sqlite":
                    from sqlalchemy.dialects.sqlite import insert

                    statement = insert(SecuritySignalBucket).values(**values)
                    statement = statement.on_conflict_do_update(
                        index_elements=[
                            "day",
                            "client_ip",
                            "signal",
                            "reason",
                            "request_target",
                        ],
                        set_={"event_count": SecuritySignalBucket.event_count + 1},
                    )
                    db.execute(statement)
                else:  # pragma: no cover - supported deployments use SQLite/PostgreSQL
                    row = db.scalar(
                        select(SecuritySignalBucket).where(
                            SecuritySignalBucket.day == values["day"],
                            SecuritySignalBucket.client_ip == values["client_ip"],
                            SecuritySignalBucket.signal == values["signal"],
                            SecuritySignalBucket.reason == values["reason"],
                            SecuritySignalBucket.request_target
                            == values["request_target"],
                        )
                    )
                    if row is None:
                        db.add(SecuritySignalBucket(**values))
                    else:
                        row.event_count += 1
                db.commit()
        except Exception:
            # Logging must never break request handling.
            return


# Compatibility export for internal imports while the implementation is now
# deliberately restricted to aggregated security signals.
DatabaseLogHandler = SecurityEventHandler
