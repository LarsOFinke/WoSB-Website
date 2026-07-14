from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.modules.admin.models.app_log import AppLog
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
THREAT_LEVELS = ("low", "guarded", "elevated", "critical")


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


def _effective_range(from_date: date | None, to_date: date | None) -> tuple[date, date]:
    today = utc_now().date()
    effective_to = to_date or today
    effective_from = from_date or (effective_to - timedelta(days=6))
    if effective_from > effective_to:
        effective_from, effective_to = effective_to, effective_from
    if (effective_to - effective_from).days > 90:
        effective_from = effective_to - timedelta(days=90)
    return effective_from, effective_to


def _client_ip(row: AppLog) -> str:
    return (row.client_ip or row.client or "unknown").strip() or "unknown"


def _load_rows(db: Session, *, from_date: date | None, to_date: date | None) -> tuple[date, date, list[AppLog]]:
    effective_from, effective_to = _effective_range(from_date, to_date)
    start = datetime.combine(effective_from, time.min)
    end = datetime.combine(effective_to + timedelta(days=1), time.min)
    rows = list(db.scalars(
        select(AppLog)
        .where(AppLog.created_at >= start, AppLog.created_at < end)
        .order_by(AppLog.created_at.asc(), AppLog.id.asc())
    ).all())
    return effective_from, effective_to, rows


def _build_ip_rows(rows: list[AppLog]) -> list[SecurityIpRow]:
    ip_data: dict[str, dict[str, object]] = defaultdict(lambda: {
        "request_count": 0,
        "status_4xx": 0,
        "status_5xx": 0,
        "warnings": 0,
        "errors": 0,
        "suspicious": 0,
        "paths": Counter(),
        "first_seen": None,
        "last_seen": None,
    })

    for row in rows:
        ip = _client_ip(row)
        item = ip_data[ip]
        item["request_count"] += 1
        item["paths"][row.path or "—"] += 1
        item["first_seen"] = row.created_at if item["first_seen"] is None else min(item["first_seen"], row.created_at)
        item["last_seen"] = row.created_at if item["last_seen"] is None else max(item["last_seen"], row.created_at)
        status = int(row.status_code or 0)
        if row.level == "WARNING":
            item["warnings"] += 1
        if row.level in {"ERROR", "CRITICAL"}:
            item["errors"] += 1
        if 400 <= status < 500:
            item["status_4xx"] += 1
        if 500 <= status < 600:
            item["status_5xx"] += 1
        if _is_suspicious(row):
            item["suspicious"] += 1

    result: list[SecurityIpRow] = []
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
        result.append(SecurityIpRow(
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
    return result


def _build_days(rows: list[AppLog], *, effective_from: date, effective_to: date) -> list[SecurityDayBucket]:
    day_data: dict[date, dict[str, object]] = defaultdict(lambda: {
        "total": 0,
        "warnings": 0,
        "errors": 0,
        "status_4xx": 0,
        "status_5xx": 0,
        "suspicious": 0,
        "ips": set(),
    })
    for row in rows:
        item = day_data[row.created_at.date()]
        item["total"] += 1
        item["ips"].add(_client_ip(row))
        status = int(row.status_code or 0)
        if row.level == "WARNING":
            item["warnings"] += 1
        if row.level in {"ERROR", "CRITICAL"}:
            item["errors"] += 1
        if 400 <= status < 500:
            item["status_4xx"] += 1
        if 500 <= status < 600:
            item["status_5xx"] += 1
        if _is_suspicious(row):
            item["suspicious"] += 1

    days: list[SecurityDayBucket] = []
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
    return days


def security_ip_addresses_for_level(
    db: Session,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    threat_level: str | None = None,
) -> set[str]:
    if not threat_level:
        return set()
    _, _, rows = _load_rows(db, from_date=from_date, to_date=to_date)
    return {
        row.client_ip
        for row in _build_ip_rows(rows)
        if row.threat_level == threat_level
    }


def build_security_dashboard(
    db: Session,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    sort: str = "threat",
    limit: int = 100,
    threat_level: str | None = None,
    client_ip: str | None = None,
) -> SecurityDashboard:
    effective_from, effective_to, rows = _load_rows(db, from_date=from_date, to_date=to_date)
    all_ip_rows = _build_ip_rows(rows)
    threat_counts = {level: 0 for level in THREAT_LEVELS}
    for row in all_ip_rows:
        threat_counts[row.threat_level] += 1

    visible_ips = [
        row for row in all_ip_rows
        if not threat_level or row.threat_level == threat_level
    ]

    key_map = {
        "requests": lambda row: (row.request_count, row.threat_score, row.last_seen),
        "last_seen": lambda row: (row.last_seen, row.threat_score, row.request_count),
        "ip": lambda row: (row.client_ip, row.threat_score),
        "threat": lambda row: (row.threat_score, row.suspicious_hits, row.request_count),
    }
    reverse = sort != "ip"
    visible_ips.sort(key=key_map.get(sort, key_map["threat"]), reverse=reverse)

    focused_ip = (client_ip or "").strip()
    metric_ip_rows = visible_ips
    if focused_ip:
        metric_ip_rows = [row for row in visible_ips if row.client_ip == focused_ip]
    allowed_ips = {row.client_ip for row in metric_ip_rows}
    filtered_rows = [row for row in rows if _client_ip(row) in allowed_ips]
    days = _build_days(filtered_rows, effective_from=effective_from, effective_to=effective_to)

    total_4xx = sum(day.status_4xx for day in days)
    total_5xx = sum(day.status_5xx for day in days)
    suspicious_hits = sum(day.suspicious for day in days)
    overall_score = max((row.threat_score for row in metric_ip_rows), default=0)
    if suspicious_hits:
        overall_score = min(100, max(overall_score, suspicious_hits * 8))

    return SecurityDashboard(
        threat_score=overall_score,
        threat_level=_threat_level(overall_score),
        total_requests=len(filtered_rows),
        unique_ips=len(metric_ip_rows),
        suspicious_hits=suspicious_hits,
        status_4xx=total_4xx,
        status_5xx=total_5xx,
        threat_counts=threat_counts,
        days=days,
        ips=visible_ips[:limit],
    )
