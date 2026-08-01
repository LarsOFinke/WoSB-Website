from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, MutableMapping

SUPPORTED_MANIFEST_SCHEMAS = frozenset({1, 2})
PRODUCTION_CONSISTENCY_MODES = frozenset({"application-quiesced", "no-running-api"})
REPORT_SCHEMA_VERSION = 1
_REVISION_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")


@dataclass(frozen=True, slots=True)
class RecoveryDescriptor:
    manifest_schema: int
    created_at: str
    application_version: str
    git_commit: str
    alembic_revisions: tuple[str, ...]
    postgres_version: str
    backup_reason: str
    backup_format: str
    backup_consistency: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["alembic_revisions"] = list(self.alembic_revisions)
        return payload


@dataclass(frozen=True, slots=True)
class CompatibilityAssessment:
    status: str
    compatible: bool
    migration_required: bool
    backup_revisions: tuple[str, ...]
    target_revisions: tuple[str, ...]
    detail: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["backup_revisions"] = list(self.backup_revisions)
        payload["target_revisions"] = list(self.target_revisions)
        return payload


@dataclass(frozen=True, slots=True)
class MigrationGraph:
    parents: Mapping[str, tuple[str, ...]]
    heads: tuple[str, ...]

    @classmethod
    def from_directory(cls, versions_directory: Path) -> "MigrationGraph":
        versions_directory = versions_directory.expanduser().resolve()
        if not versions_directory.is_dir():
            raise RuntimeError(f"Alembic migration directory does not exist: {versions_directory}")
        parents: dict[str, tuple[str, ...]] = {}
        children: dict[str, set[str]] = {}
        for path in sorted(versions_directory.glob("*.py")):
            revision, down_revisions = _read_migration_assignments(path)
            if revision in parents:
                raise RuntimeError(f"Duplicate Alembic revision: {revision}")
            parents[revision] = down_revisions
            children.setdefault(revision, set())
            for parent in down_revisions:
                children.setdefault(parent, set()).add(revision)
        if not parents:
            raise RuntimeError(f"No Alembic migrations found in: {versions_directory}")
        missing = sorted(
            parent
            for revision_parents in parents.values()
            for parent in revision_parents
            if parent not in parents
        )
        if missing:
            raise RuntimeError(f"Alembic graph references missing revisions: {', '.join(missing)}")
        heads = tuple(sorted(revision for revision in parents if not children.get(revision)))
        if not heads:
            raise RuntimeError("Alembic migration graph has no head.")
        _assert_acyclic(parents)
        return cls(parents=parents, heads=heads)

    @property
    def revisions(self) -> frozenset[str]:
        return frozenset(self.parents)

    def ancestors_including_self(self, revisions: Iterable[str]) -> frozenset[str]:
        pending = list(revisions)
        seen: set[str] = set()
        while pending:
            revision = pending.pop()
            if revision in seen:
                continue
            if revision not in self.parents:
                raise RuntimeError(f"Unknown Alembic revision: {revision}")
            seen.add(revision)
            pending.extend(self.parents[revision])
        return frozenset(seen)


def _literal_assignment(tree: ast.Module, name: str) -> Any:
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == name for target in targets):
                value = node.value
                if value is None:
                    return None
                try:
                    return ast.literal_eval(value)
                except (ValueError, TypeError) as exc:
                    raise RuntimeError(f"Migration assignment {name} must be a literal.") from exc
    raise RuntimeError(f"Migration has no {name} assignment.")


def _normalize_revisions(value: Any, *, label: str) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    values = (value,) if isinstance(value, str) else tuple(value) if isinstance(value, (list, tuple)) else ()
    if not values:
        raise RuntimeError(f"{label} must be a revision string or sequence.")
    normalized: list[str] = []
    for item in values:
        revision = str(item).strip()
        if not _REVISION_RE.fullmatch(revision):
            raise RuntimeError(f"Invalid Alembic revision in {label}: {revision!r}")
        if revision not in normalized:
            normalized.append(revision)
    return tuple(normalized)


def _read_migration_assignments(path: Path) -> tuple[str, tuple[str, ...]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        raise RuntimeError(f"Could not parse migration: {path.name}") from exc
    revision_values = _normalize_revisions(_literal_assignment(tree, "revision"), label="revision")
    if len(revision_values) != 1:
        raise RuntimeError(f"Migration must define exactly one revision: {path.name}")
    down_revisions = _normalize_revisions(
        _literal_assignment(tree, "down_revision"), label="down_revision"
    )
    return revision_values[0], down_revisions


def _assert_acyclic(parents: Mapping[str, tuple[str, ...]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(revision: str) -> None:
        if revision in visiting:
            raise RuntimeError(f"Alembic migration graph contains a cycle at: {revision}")
        if revision in visited:
            return
        visiting.add(revision)
        for parent in parents[revision]:
            visit(parent)
        visiting.remove(revision)
        visited.add(revision)

    for revision in parents:
        visit(revision)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _revision_values(value: Any) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, str):
        raw = [part.strip() for part in value.split(",")]
    elif isinstance(value, (list, tuple)):
        raw = [str(part).strip() for part in value]
    else:
        raise RuntimeError("Alembic revisions must be a string or sequence.")
    revisions: list[str] = []
    for revision in raw:
        if not revision:
            continue
        if not _REVISION_RE.fullmatch(revision):
            raise RuntimeError(f"Invalid Alembic revision in recovery manifest: {revision!r}")
        if revision not in revisions:
            revisions.append(revision)
    return tuple(revisions)


def descriptor_from_manifest(manifest: Mapping[str, Any]) -> RecoveryDescriptor:
    schema = int(manifest.get("schema_version", -1))
    if schema not in SUPPORTED_MANIFEST_SCHEMAS:
        raise RuntimeError(f"Unsupported recovery manifest schema: {schema}")
    application = _mapping(manifest.get("application"))
    database = _mapping(manifest.get("database"))
    backup = _mapping(manifest.get("backup"))
    revisions = _revision_values(
        application.get("alembic_revisions") or application.get("alembic_head")
    )
    return RecoveryDescriptor(
        manifest_schema=schema,
        created_at=str(manifest.get("created_at") or ""),
        application_version=str(application.get("version") or ""),
        git_commit=str(application.get("git_commit") or ""),
        alembic_revisions=revisions,
        postgres_version=str(database.get("postgres_version") or ""),
        backup_reason=str(backup.get("reason") or ""),
        backup_format=str(backup.get("format") or ""),
        backup_consistency=str(backup.get("consistency") or "unrecorded"),
    )


def is_production_consistent(descriptor: RecoveryDescriptor) -> bool:
    return descriptor.backup_consistency in PRODUCTION_CONSISTENCY_MODES


def assess_compatibility(
    descriptor: RecoveryDescriptor,
    graph: MigrationGraph,
    *,
    allow_unrecorded: bool = False,
) -> CompatibilityAssessment:
    backup = descriptor.alembic_revisions
    target = graph.heads
    if not backup:
        return CompatibilityAssessment(
            status="unrecorded",
            compatible=allow_unrecorded,
            migration_required=True,
            backup_revisions=(),
            target_revisions=target,
            detail=(
                "Backup does not record an Alembic revision; runtime staging validation is required."
                if allow_unrecorded
                else "Backup does not record an Alembic revision and is rejected by fail-closed policy."
            ),
        )
    unknown = sorted(set(backup) - graph.revisions)
    if unknown:
        return CompatibilityAssessment(
            status="unknown_revision",
            compatible=False,
            migration_required=False,
            backup_revisions=backup,
            target_revisions=target,
            detail=f"Backup references revisions not present in this checkout: {', '.join(unknown)}.",
        )
    if set(backup) == set(target):
        return CompatibilityAssessment(
            status="same",
            compatible=True,
            migration_required=False,
            backup_revisions=backup,
            target_revisions=target,
            detail="Backup schema already matches the current Alembic head.",
        )
    target_ancestors = graph.ancestors_including_self(target)
    if set(backup).issubset(target_ancestors):
        return CompatibilityAssessment(
            status="upgrade",
            compatible=True,
            migration_required=True,
            backup_revisions=backup,
            target_revisions=target,
            detail="Backup schema is an ancestor of the current head and can be migrated forward.",
        )
    backup_ancestors = graph.ancestors_including_self(backup)
    if set(target).issubset(backup_ancestors):
        return CompatibilityAssessment(
            status="backup_newer",
            compatible=False,
            migration_required=False,
            backup_revisions=backup,
            target_revisions=target,
            detail="Backup schema is newer than this checkout; automatic downgrade is forbidden.",
        )
    return CompatibilityAssessment(
        status="diverged",
        compatible=False,
        migration_required=False,
        backup_revisions=backup,
        target_revisions=target,
        detail="Backup and checkout are on divergent Alembic branches.",
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_report(
    *,
    mode: str,
    source: str,
    descriptor: RecoveryDescriptor | None = None,
    source_artifact: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "mode": mode,
        "source": source,
        "started_at": _utc_now(),
        "finished_at": "",
        "status": "running",
        "recoverable": False,
        "descriptor": descriptor.to_dict() if descriptor else {},
        "checks": [],
    }
    if source_artifact:
        report["source_artifact"] = dict(source_artifact)
    return report


def add_report_check(
    report: MutableMapping[str, Any],
    *,
    name: str,
    status: str,
    detail: str = "",
    data: Mapping[str, Any] | None = None,
) -> None:
    if status not in {"passed", "failed", "warning", "skipped"}:
        raise ValueError(f"Unsupported report status: {status}")
    checks = report.setdefault("checks", [])
    if not isinstance(checks, list):
        raise ValueError("Recovery report checks must be a list.")
    check: dict[str, Any] = {
        "name": name,
        "status": status,
        "detail": detail,
        "recorded_at": _utc_now(),
    }
    if data:
        check["data"] = dict(data)
    checks.append(check)


def finalize_report(
    report: MutableMapping[str, Any],
    *,
    status: str,
    recoverable: bool,
) -> None:
    if status not in {"passed", "failed", "aborted"}:
        raise ValueError(f"Unsupported final report status: {status}")
    report["status"] = status
    report["recoverable"] = bool(recoverable)
    report["finished_at"] = _utc_now()


def write_report(path: Path, report: Mapping[str, Any]) -> Path:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    try:
        temporary.chmod(0o600)
    except OSError:
        pass
    temporary.replace(path)
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path
