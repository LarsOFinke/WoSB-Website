from __future__ import annotations

import logging
from datetime import datetime, timezone


class DatabaseLogHandler(logging.Handler):
    """Persist application logs for the admin dashboard.

    The handler is intentionally attached only to the ``app`` logger tree to
    avoid storing noisy dependency/SQL logs. Failures are swallowed because
    logging must never break request handling.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            from app.db.session import SessionLocal
            from app.modules.admin.models.app_log import AppLog

            with SessionLocal() as db:
                entry = AppLog(
                    created_at=datetime.fromtimestamp(record.created, tz=timezone.utc).replace(tzinfo=None),
                    level=record.levelname,
                    logger=record.name[:120],
                    message=record.getMessage(),
                    request_id=getattr(record, "request_id", None),
                    method=getattr(record, "method", None),
                    path=getattr(record, "path", None),
                    status_code=getattr(record, "status_code", None),
                    duration_ms=getattr(record, "duration_ms", None),
                    client=getattr(record, "client", None),
                    client_ip=getattr(record, "client_ip", None),
                    forwarded_for=getattr(record, "forwarded_for", None),
                    user_agent=getattr(record, "user_agent", None),
                    query_string=getattr(record, "query_string", None),
                    exception=logging.Formatter().formatException(record.exc_info) if record.exc_info else None,
                )
                db.add(entry)
                db.commit()
        except Exception:
            return
