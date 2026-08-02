from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class SecurityDayBucket(BaseModel):
    day: date
    total_events: int
    unique_ips: int
    reconnaissance: int
    login_failures: int
    rate_limits: int


class SecurityReasonBreakdown(BaseModel):
    signal: str
    reason: str
    request_target: str
    event_count: int


class SecurityIpRow(BaseModel):
    client_ip: str
    threat_score: int = Field(ge=0, le=100)
    threat_level: str
    event_count: int
    reconnaissance: int
    login_failures: int
    rate_limits: int
    reconnaissance_points: int
    login_failure_points: int
    rate_limit_points: int
    volume_bonus: int
    first_seen: date
    last_seen: date
    reasons: list[SecurityReasonBreakdown] = Field(default_factory=list)


class SecurityDashboard(BaseModel):
    threat_score: int = Field(ge=0, le=100)
    threat_level: str
    total_events: int
    unique_ips: int
    threat_counts: dict[str, int] = Field(default_factory=dict)
    signal_counts: dict[str, int] = Field(default_factory=dict)
    days: list[SecurityDayBucket] = Field(default_factory=list)
    ips: list[SecurityIpRow] = Field(default_factory=list)
