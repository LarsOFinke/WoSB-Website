from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.modules.admin.models.app_log import AppLog
from app.modules.admin.schemas.security_dashboard import (
    SecurityDashboard,
    SecurityDayBucket,
    SecurityIpRow,
)

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


class ThreatScorer:
    def is_suspicious(self, row: AppLog) -> bool:
        path = (row.path or "").lower()
        query = (row.query_string or "").lower()
        user_agent = (row.user_agent or "").lower()
        return (
            any(part in path or part in query for part in SUSPICIOUS_PATH_PARTS)
            or "sqlmap" in user_agent
        )

    @staticmethod
    def level(score: int) -> str:
        if score >= 70:
            return "critical"
        if score >= 45:
            return "elevated"
        if score >= 20:
            return "guarded"
        return "low"

    @staticmethod
    def score(
        *,
        request_count: int,
        status_4xx: int,
        status_5xx: int,
        warnings: int,
        errors: int,
        suspicious: int,
        distinct_paths: int,
    ) -> int:
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


class SecurityDashboardService:
    def __init__(self, db: Session, scorer: ThreatScorer | None = None) -> None:
        self.db = db
        self.scorer = scorer or ThreatScorer()

    def ip_addresses_for_level(
        self,
        *,
        from_date: date | None = None,
        to_date: date | None = None,
        threat_level: str | None = None,
    ) -> set[str]:
        if not threat_level:
            return set()
        _, _, rows = self._load_rows(from_date=from_date, to_date=to_date)
        return {
            row.client_ip
            for row in self._build_ip_rows(rows)
            if row.threat_level == threat_level
        }

    def build(
        self,
        *,
        from_date: date | None = None,
        to_date: date | None = None,
        sort: str = "threat",
        limit: int = 100,
        threat_level: str | None = None,
        client_ip: str | None = None,
    ) -> SecurityDashboard:
        effective_from, effective_to, rows = self._load_rows(
            from_date=from_date, to_date=to_date
        )
        all_ip_rows = self._build_ip_rows(rows)
        threat_counts = {level: 0 for level in THREAT_LEVELS}
        for row in all_ip_rows:
            threat_counts[row.threat_level] += 1

        visible_ips = [
            row
            for row in all_ip_rows
            if not threat_level or row.threat_level == threat_level
        ]
        self._sort_ip_rows(visible_ips, sort)

        focused_ip = (client_ip or "").strip()
        metric_ip_rows = (
            [row for row in visible_ips if row.client_ip == focused_ip]
            if focused_ip
            else visible_ips
        )
        allowed_ips = {row.client_ip for row in metric_ip_rows}
        filtered_rows = [row for row in rows if self._client_ip(row) in allowed_ips]
        days = self._build_days(
            filtered_rows,
            effective_from=effective_from,
            effective_to=effective_to,
        )
        suspicious_hits = sum(day.suspicious for day in days)
        overall_score = max((row.threat_score for row in metric_ip_rows), default=0)
        if suspicious_hits:
            overall_score = min(100, max(overall_score, suspicious_hits * 8))

        return SecurityDashboard(
            threat_score=overall_score,
            threat_level=self.scorer.level(overall_score),
            total_requests=len(filtered_rows),
            unique_ips=len(metric_ip_rows),
            suspicious_hits=suspicious_hits,
            status_4xx=sum(day.status_4xx for day in days),
            status_5xx=sum(day.status_5xx for day in days),
            threat_counts=threat_counts,
            days=days,
            ips=visible_ips[:limit],
        )

    def _load_rows(
        self, *, from_date: date | None, to_date: date | None
    ) -> tuple[date, date, list[AppLog]]:
        effective_from, effective_to = self._effective_range(from_date, to_date)
        start = datetime.combine(effective_from, time.min)
        end = datetime.combine(effective_to + timedelta(days=1), time.min)
        rows = list(
            self.db.scalars(
                select(AppLog)
                .where(AppLog.created_at >= start, AppLog.created_at < end)
                .order_by(AppLog.created_at.asc(), AppLog.id.asc())
            ).all()
        )
        return effective_from, effective_to, rows

    def _build_ip_rows(self, rows: list[AppLog]) -> list[SecurityIpRow]:
        data: dict[str, dict[str, Any]] = defaultdict(self._empty_ip_bucket)
        for row in rows:
            item = data[self._client_ip(row)]
            self._consume_row(item, row)

        result: list[SecurityIpRow] = []
        for client_ip, item in data.items():
            distinct_paths = len(item["paths"])
            score = self.scorer.score(
                request_count=item["request_count"],
                status_4xx=item["status_4xx"],
                status_5xx=item["status_5xx"],
                warnings=item["warnings"],
                errors=item["errors"],
                suspicious=item["suspicious"],
                distinct_paths=distinct_paths,
            )
            result.append(
                SecurityIpRow(
                    client_ip=client_ip,
                    threat_score=score,
                    threat_level=self.scorer.level(score),
                    request_count=item["request_count"],
                    distinct_paths=distinct_paths,
                    status_4xx=item["status_4xx"],
                    status_5xx=item["status_5xx"],
                    warnings=item["warnings"],
                    errors=item["errors"],
                    suspicious_hits=item["suspicious"],
                    first_seen=item["first_seen"],
                    last_seen=item["last_seen"],
                    top_paths=[path for path, _ in item["paths"].most_common(3)],
                )
            )
        return result

    def _build_days(
        self,
        rows: list[AppLog],
        *,
        effective_from: date,
        effective_to: date,
    ) -> list[SecurityDayBucket]:
        data: dict[date, dict[str, Any]] = defaultdict(self._empty_day_bucket)
        for row in rows:
            item = data[row.created_at.date()]
            item["total"] += 1
            item["ips"].add(self._client_ip(row))
            self._consume_status(item, row)

        days: list[SecurityDayBucket] = []
        cursor = effective_from
        while cursor <= effective_to:
            item = data[cursor]
            days.append(
                SecurityDayBucket(
                    day=cursor,
                    total=item["total"],
                    warnings=item["warnings"],
                    errors=item["errors"],
                    status_4xx=item["status_4xx"],
                    status_5xx=item["status_5xx"],
                    suspicious=item["suspicious"],
                    unique_ips=len(item["ips"]),
                )
            )
            cursor += timedelta(days=1)
        return days

    def _consume_row(self, item: dict[str, Any], row: AppLog) -> None:
        item["request_count"] += 1
        item["paths"][row.path or "—"] += 1
        item["first_seen"] = (
            row.created_at
            if item["first_seen"] is None
            else min(item["first_seen"], row.created_at)
        )
        item["last_seen"] = (
            row.created_at
            if item["last_seen"] is None
            else max(item["last_seen"], row.created_at)
        )
        self._consume_status(item, row)

    def _consume_status(self, item: dict[str, Any], row: AppLog) -> None:
        status = int(row.status_code or 0)
        if row.level == "WARNING":
            item["warnings"] += 1
        if row.level in {"ERROR", "CRITICAL"}:
            item["errors"] += 1
        if 400 <= status < 500:
            item["status_4xx"] += 1
        if 500 <= status < 600:
            item["status_5xx"] += 1
        if self.scorer.is_suspicious(row):
            item["suspicious"] += 1

    @staticmethod
    def _effective_range(
        from_date: date | None, to_date: date | None
    ) -> tuple[date, date]:
        today = utc_now().date()
        effective_to = to_date or today
        effective_from = from_date or (effective_to - timedelta(days=6))
        if effective_from > effective_to:
            effective_from, effective_to = effective_to, effective_from
        if (effective_to - effective_from).days > 90:
            effective_from = effective_to - timedelta(days=90)
        return effective_from, effective_to

    @staticmethod
    def _client_ip(row: AppLog) -> str:
        return (row.client_ip or row.client or "unknown").strip() or "unknown"

    @staticmethod
    def _empty_ip_bucket() -> dict[str, Any]:
        return {
            "request_count": 0,
            "status_4xx": 0,
            "status_5xx": 0,
            "warnings": 0,
            "errors": 0,
            "suspicious": 0,
            "paths": Counter(),
            "first_seen": None,
            "last_seen": None,
        }

    @staticmethod
    def _empty_day_bucket() -> dict[str, Any]:
        return {
            "total": 0,
            "warnings": 0,
            "errors": 0,
            "status_4xx": 0,
            "status_5xx": 0,
            "suspicious": 0,
            "ips": set(),
        }

    @staticmethod
    def _sort_ip_rows(rows: list[SecurityIpRow], sort: str) -> None:
        key_map = {
            "requests": lambda row: (row.request_count, row.threat_score, row.last_seen),
            "last_seen": lambda row: (row.last_seen, row.threat_score, row.request_count),
            "ip": lambda row: (row.client_ip, row.threat_score),
            "threat": lambda row: (
                row.threat_score,
                row.suspicious_hits,
                row.request_count,
            ),
        }
        rows.sort(key=key_map.get(sort, key_map["threat"]), reverse=sort != "ip")


def security_ip_addresses_for_level(db: Session, **kwargs) -> set[str]:
    return SecurityDashboardService(db).ip_addresses_for_level(**kwargs)


def build_security_dashboard(db: Session, **kwargs) -> SecurityDashboard:
    return SecurityDashboardService(db).build(**kwargs)


__all__ = [
    "SecurityDashboardService",
    "ThreatScorer",
    "build_security_dashboard",
    "security_ip_addresses_for_level",
]
