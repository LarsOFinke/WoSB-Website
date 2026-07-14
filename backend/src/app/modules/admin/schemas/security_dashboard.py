from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class SecurityDayBucket(BaseModel):
    day: date
    total: int
    warnings: int
    errors: int
    status_4xx: int
    status_5xx: int
    suspicious: int
    unique_ips: int


class SecurityIpRow(BaseModel):
    client_ip: str
    threat_score: int = Field(ge=0, le=100)
    threat_level: str
    request_count: int
    distinct_paths: int
    status_4xx: int
    status_5xx: int
    warnings: int
    errors: int
    suspicious_hits: int
    first_seen: datetime
    last_seen: datetime
    top_paths: list[str] = Field(default_factory=list)


class SecurityDashboard(BaseModel):
    threat_score: int = Field(ge=0, le=100)
    threat_level: str
    total_requests: int
    unique_ips: int
    suspicious_hits: int
    status_4xx: int
    status_5xx: int
    threat_counts: dict[str, int] = Field(default_factory=dict)
    days: list[SecurityDayBucket] = Field(default_factory=list)
    ips: list[SecurityIpRow] = Field(default_factory=list)
