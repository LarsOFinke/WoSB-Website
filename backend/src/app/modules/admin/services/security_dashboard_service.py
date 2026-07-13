from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.admin.models.app_log import AppLog
from app.core.time import utc_now
from app.modules.admin.schemas.security_dashboard import SecurityDashboard, SecurityDayBucket, SecurityIpRow

SUSPICIOUS_PATH_PARTS = (
    "/.env",
    "/.git",
    "/wp-admin",
    "/wp-login",
    "/vendor/phpunit",
    "/phpunit",
    "/cgi-bin",
    "/adminer",
    "/server-status",
    "/etc/passwd",
    "/actuator",
    ".php",
)


def _is_suspicious(row: AppLog) -> bool:
    path = (row.path or "").lower()
    query = (row.query_string or "").lower()
    user_agent = (row.user_agent or "").lower()
    return any(part in path or part in query for part in SUSPICIOUS_PATH_PARTS) or "sqlmap" in user_agent


def _threat_level(score: int) -> str:
    if score >= 70:
        return "critical"
    if score >= 45:
        return "elevated"
    if score >= 20:
        return "guarded"
    return "low"


def _score(*, request_count: int, status_4xx: int, status_5xx: int, warnings: int, errors: int, suspicious: int, distinct_paths: int) -> int:
    raw = (
        suspicious * 18
        + errors * 10
        + status_5xx * 8
        + warnings * 3
        + min(status_4xx, 25)
        + min(max(distinct_paths - 8, 0), 15)
        + min(max(request_count - 100, 0) // 25, 8)
    )
    return min(100, int(raw))


def build_security_dashboard(
    db: Session,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    sort: str = "threat",
    limit: int = 100,
) -> SecurityDashboard:
    today = utc_now().date()
    effective_to = to_date or today
    effective_from = from_date or (effective_to - timedelta(days=6))
    if effective_from > effective_to:
        effective_from, effective_to = effective_to, effective_from
    if (effective_to - effective_from).days > 90:
        effective_from = effective_to - timedelta(days=90)

    start = datetime.combine(effective_from, time.min)
    end = datetime.combine(effective_to + timedelta(days=1), time.min)
    rows = db.scalars(
        select(AppLog)
        .where(AppLog.created_at >= start, AppLog.created_at < end)
        .order_by(AppLog.created_at.asc(), AppLog.id.asc())
    ).all()

    day_data: dict[date, dict[str, object]] = defaultdict(lambda: {
        "total": 0, "warnings": 0, "errors": 0, "status_4xx": 0, "status_5xx": 0, "suspicious": 0, "ips": set()
    })
    ip_data: dict[str, dict[str, object]] = defaultdict(lambda: {
        "request_count": 0, "status_4xx": 0, "status_5xx": 0, "warnings": 0, "errors": 0,
        "suspicious": 0, "paths": Counter(), "first_seen": None, "last_seen": None,
    })

    for row in rows:
        day = row.created_at.date()
        day_row = day_data[day]
        day_row["total"] += 1
        ip = (row.client_ip or row.client or "unknown").strip() or "unknown"
        day_row["ips"].add(ip)
        status = int(row.status_code or 0)
        suspicious = _is_suspicious(row)
        if row.level == "WARNING":
            day_row["warnings"] += 1
        if row.level in {"ERROR", "CRITICAL"}:
            day_row["errors"] += 1
        if 400 <= status < 500:
            day_row["status_4xx"] += 1
        if 500 <= status < 600:
            day_row["status_5xx"] += 1
        if suspicious:
            day_row["suspicious"] += 1

        ip_row = ip_data[ip]
        ip_row["request_count"] += 1
        ip_row["paths"][row.path or "—"] += 1
        ip_row["first_seen"] = row.created_at if ip_row["first_seen"] is None else min(ip_row["first_seen"], row.created_at)
        ip_row["last_seen"] = row.created_at if ip_row["last_seen"] is None else max(ip_row["last_seen"], row.created_at)
        if row.level == "WARNING":
            ip_row["warnings"] += 1
        if row.level in {"ERROR", "CRITICAL"}:
            ip_row["errors"] += 1
        if 400 <= status < 500:
            ip_row["status_4xx"] += 1
        if 500 <= status < 600:
            ip_row["status_5xx"] += 1
        if suspicious:
            ip_row["suspicious"] += 1

    days = []
    cursor = effective_from
    while cursor <= effective_to:
        item = day_data[cursor]
        days.append(SecurityDayBucket(
            day=cursor,
            total=int(item["total"]),
            warnings=int(item["warnings"]),
            errors=int(item["errors"]),
            status_4xx=int(item["status_4xx"]),
            status_5xx=int(item["status_5xx"]),
            suspicious=int(item["suspicious"]),
            unique_ips=len(item["ips"]),
        ))
        cursor += timedelta(days=1)

    ips: list[SecurityIpRow] = []
    for ip, item in ip_data.items():
        distinct_paths = len(item["paths"])
        score = _score(
            request_count=int(item["request_count"]),
            status_4xx=int(item["status_4xx"]),
            status_5xx=int(item["status_5xx"]),
            warnings=int(item["warnings"]),
            errors=int(item["errors"]),
            suspicious=int(item["suspicious"]),
            distinct_paths=distinct_paths,
        )
        ips.append(SecurityIpRow(
            client_ip=ip,
            threat_score=score,
            threat_level=_threat_level(score),
            request_count=int(item["request_count"]),
            distinct_paths=distinct_paths,
            status_4xx=int(item["status_4xx"]),
            status_5xx=int(item["status_5xx"]),
            warnings=int(item["warnings"]),
            errors=int(item["errors"]),
            suspicious_hits=int(item["suspicious"]),
            first_seen=item["first_seen"],
            last_seen=item["last_seen"],
            top_paths=[path for path, _ in item["paths"].most_common(3)],
        ))

    key_map = {
        "requests": lambda row: (row.request_count, row.threat_score, row.last_seen),
        "last_seen": lambda row: (row.last_seen, row.threat_score, row.request_count),
        "ip": lambda row: (row.client_ip, row.threat_score),
        "threat": lambda row: (row.threat_score, row.suspicious_hits, row.request_count),
    }
    reverse = sort != "ip"
    ips.sort(key=key_map.get(sort, key_map["threat"]), reverse=reverse)
    ips = ips[:limit]

    total_4xx = sum(day.status_4xx for day in days)
    total_5xx = sum(day.status_5xx for day in days)
    suspicious_hits = sum(day.suspicious for day in days)
    overall_score = max((row.threat_score for row in ips), default=0)
    if suspicious_hits:
        overall_score = min(100, max(overall_score, suspicious_hits * 8))

    return SecurityDashboard(
        threat_score=overall_score,
        threat_level=_threat_level(overall_score),
        total_requests=len(rows),
        unique_ips=len(ip_data),
        suspicious_hits=suspicious_hits,
        status_4xx=total_4xx,
        status_5xx=total_5xx,
        days=days,
        ips=ips,
    )
