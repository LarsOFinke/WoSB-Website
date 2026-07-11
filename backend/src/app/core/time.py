"""Time helpers shared by persistence and domain services.

The database schema stores UTC timestamps without timezone metadata for SQLite
and PostgreSQL compatibility. Centralising the conversion keeps that legacy
contract explicit while avoiding deprecated ``datetime.utcnow`` calls.
"""


from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current UTC time as a naive datetime for database columns."""

    return datetime.now(UTC).replace(tzinfo=None)
