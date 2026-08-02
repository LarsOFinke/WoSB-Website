from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.modules.admin.models.security_event import (
    SECURITY_SIGNAL_LOGIN_FAILURE,
    SECURITY_SIGNAL_RATE_LIMIT,
    SECURITY_SIGNAL_RECONNAISSANCE,
    SecuritySignalBucket,
)
from app.modules.admin.schemas.security_dashboard import (
    SecurityDashboard,
    SecurityDayBucket,
    SecurityIpRow,
)
from app.modules.admin.services.ip_block_service import active_blocked_ip_addresses

THREAT_LEVELS = ("low", "guarded", "elevated", "critical")
SIGNAL_WEIGHTS = {
    SECURITY_SIGNAL_RECONNAISSANCE: 25,
    SECURITY_SIGNAL_LOGIN_FAILURE: 6,
    SECURITY_SIGNAL_RATE_LIMIT: 15,
}


class ThreatScorer:
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
    def score(signals: Counter[str]) -> int:
        weighted = sum(SIGNAL_WEIGHTS.get(signal, 0) * count for signal, count in signals.items())
        volume_bonus = ThreatScorer.volume_bonus(signals)
        return min(100, weighted + volume_bonus)

    @staticmethod
    def volume_bonus(signals: Counter[str]) -> int:
        return min(max(sum(signals.values()) - 3, 0) * 2, 20)


class SecurityDashboardService:
    def __init__(self, db: Session, scorer: ThreatScorer | None = None) -> None:
        self.db = db
        self.scorer = scorer or ThreatScorer()

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
            from_date=from_date,
            to_date=to_date,
        )
        all_ip_rows = self._build_ip_rows(rows)
        threat_counts = {level: 0 for level in THREAT_LEVELS}
        for row in all_ip_rows:
            threat_counts[row.threat_level] += 1

        visible_ips = [
            row for row in all_ip_rows if not threat_level or row.threat_level == threat_level
        ]
        self._sort_ip_rows(visible_ips, sort)

        focused_ip = (client_ip or "").strip()
        metric_ip_rows = (
            [row for row in visible_ips if row.client_ip == focused_ip]
            if focused_ip
            else visible_ips
        )
        allowed_ips = {row.client_ip for row in metric_ip_rows}
        filtered_rows = [row for row in rows if row.client_ip in allowed_ips]
        days = self._build_days(
            filtered_rows,
            effective_from=effective_from,
            effective_to=effective_to,
        )
        signal_counts: Counter[str] = Counter()
        for row in filtered_rows:
            signal_counts[row.signal] += row.event_count
        overall_score = max((row.threat_score for row in metric_ip_rows), default=0)

        return SecurityDashboard(
            threat_score=overall_score,
            threat_level=self.scorer.level(overall_score),
            total_events=sum(row.event_count for row in filtered_rows),
            unique_ips=len(metric_ip_rows),
            threat_counts=threat_counts,
            signal_counts={signal: int(signal_counts.get(signal, 0)) for signal in SIGNAL_WEIGHTS},
            days=days,
            ips=visible_ips[:limit],
        )

    def _load_rows(
        self,
        *,
        from_date: date | None,
        to_date: date | None,
    ) -> tuple[date, date, list[SecuritySignalBucket]]:
        effective_from, effective_to = self._effective_range(from_date, to_date)
        blocked_ips = active_blocked_ip_addresses(self.db)
        query = select(SecuritySignalBucket).where(
            SecuritySignalBucket.day >= effective_from,
            SecuritySignalBucket.day <= effective_to,
        )
        if blocked_ips:
            query = query.where(SecuritySignalBucket.client_ip.not_in(blocked_ips))
        rows = list(
            self.db.scalars(
                query.order_by(
                    SecuritySignalBucket.day.asc(),
                    SecuritySignalBucket.id.asc(),
                )
            ).all()
        )
        return effective_from, effective_to, rows

    def _build_ip_rows(self, rows: list[SecuritySignalBucket]) -> list[SecurityIpRow]:
        data: dict[str, dict[str, Any]] = defaultdict(self._empty_ip_bucket)
        for row in rows:
            item = data[row.client_ip]
            item["signals"][row.signal] += row.event_count
            item["first_seen"] = (
                row.day if item["first_seen"] is None else min(item["first_seen"], row.day)
            )
            item["last_seen"] = (
                row.day if item["last_seen"] is None else max(item["last_seen"], row.day)
            )

        result: list[SecurityIpRow] = []
        for client_ip, item in data.items():
            signals: Counter[str] = item["signals"]
            score = self.scorer.score(signals)
            result.append(
                SecurityIpRow(
                    client_ip=client_ip,
                    threat_score=score,
                    threat_level=self.scorer.level(score),
                    event_count=sum(signals.values()),
                    reconnaissance=signals[SECURITY_SIGNAL_RECONNAISSANCE],
                    login_failures=signals[SECURITY_SIGNAL_LOGIN_FAILURE],
                    rate_limits=signals[SECURITY_SIGNAL_RATE_LIMIT],
                    reconnaissance_points=(
                        signals[SECURITY_SIGNAL_RECONNAISSANCE]
                        * SIGNAL_WEIGHTS[SECURITY_SIGNAL_RECONNAISSANCE]
                    ),
                    login_failure_points=(
                        signals[SECURITY_SIGNAL_LOGIN_FAILURE]
                        * SIGNAL_WEIGHTS[SECURITY_SIGNAL_LOGIN_FAILURE]
                    ),
                    rate_limit_points=(
                        signals[SECURITY_SIGNAL_RATE_LIMIT]
                        * SIGNAL_WEIGHTS[SECURITY_SIGNAL_RATE_LIMIT]
                    ),
                    volume_bonus=self.scorer.volume_bonus(signals),
                    first_seen=item["first_seen"],
                    last_seen=item["last_seen"],
                )
            )
        return result

    def _build_days(
        self,
        rows: list[SecuritySignalBucket],
        *,
        effective_from: date,
        effective_to: date,
    ) -> list[SecurityDayBucket]:
        data: dict[date, dict[str, Any]] = defaultdict(self._empty_day_bucket)
        for row in rows:
            item = data[row.day]
            item["total_events"] += row.event_count
            item["ips"].add(row.client_ip)
            item["signals"][row.signal] += row.event_count

        days: list[SecurityDayBucket] = []
        cursor = effective_from
        while cursor <= effective_to:
            item = data[cursor]
            days.append(
                SecurityDayBucket(
                    day=cursor,
                    total_events=item["total_events"],
                    unique_ips=len(item["ips"]),
                    reconnaissance=item["signals"][SECURITY_SIGNAL_RECONNAISSANCE],
                    login_failures=item["signals"][SECURITY_SIGNAL_LOGIN_FAILURE],
                    rate_limits=item["signals"][SECURITY_SIGNAL_RATE_LIMIT],
                )
            )
            cursor += timedelta(days=1)
        return days

    @staticmethod
    def _effective_range(from_date: date | None, to_date: date | None) -> tuple[date, date]:
        today = utc_now().date()
        effective_to = min(to_date or today, today)
        effective_from = from_date or (effective_to - timedelta(days=6))
        if effective_from > effective_to:
            effective_from, effective_to = effective_to, effective_from
        # Security signals are retained briefly; the API never presents more
        # than 30 calendar days even if a client submits older dates.
        if (effective_to - effective_from).days > 29:
            effective_from = effective_to - timedelta(days=29)
        return effective_from, effective_to

    @staticmethod
    def _empty_ip_bucket() -> dict[str, Any]:
        return {"signals": Counter(), "first_seen": None, "last_seen": None}

    @staticmethod
    def _empty_day_bucket() -> dict[str, Any]:
        return {"total_events": 0, "signals": Counter(), "ips": set()}

    @staticmethod
    def _sort_ip_rows(rows: list[SecurityIpRow], sort: str) -> None:
        key_map = {
            "events": lambda row: (row.event_count, row.threat_score, row.last_seen),
            "last_seen": lambda row: (row.last_seen, row.threat_score, row.event_count),
            "ip": lambda row: (row.client_ip, row.threat_score),
            "threat": lambda row: (
                row.threat_score,
                row.reconnaissance,
                row.event_count,
            ),
        }
        rows.sort(key=key_map.get(sort, key_map["threat"]), reverse=sort != "ip")


def build_security_dashboard(db: Session, **kwargs) -> SecurityDashboard:
    return SecurityDashboardService(db).build(**kwargs)


__all__ = ["SecurityDashboardService", "ThreatScorer", "build_security_dashboard"]
