#!/usr/bin/env python3
"""Offline structural checks for the native Spring backend."""
from __future__ import annotations
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
JAVA = ROOT / "spring-api/src/main/java"
CONTRACT = ROOT / "contracts/api-contract.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"[spring-audit] {message}")


def operation_ids() -> set[str]:
    document = json.loads(CONTRACT.read_text(encoding="utf-8"))
    result: set[str] = set()
    for path_item in document["paths"].values():
        for operation in path_item.values():
            if isinstance(operation, dict) and operation.get("operationId"):
                result.add(operation["operationId"])
    return result


ops = operation_ids()
handlers: dict[str, list[Path]] = defaultdict(list)
for path in JAVA.rglob("*OperationHandler.java"):
    source = path.read_text(encoding="utf-8")
    for operation in ops.intersection(re.findall(r'"([a-zA-Z0-9_]+)"', source)):
        handlers[operation].append(path.relative_to(ROOT))
missing = sorted(ops - handlers.keys())
duplicates = {operation: paths for operation, paths in handlers.items() if len(paths) != 1}
require(not missing, f"missing operation handlers: {', '.join(missing[:10])}")
require(not duplicates, "duplicate operation handlers: " + ", ".join(sorted(duplicates)[:10]))

all_java = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in JAVA.rglob("*.java"))
for forbidden in ("FastApiProxy", "FASTAPI_INTERNAL_URL", "http://api:8000", "FetchType.EAGER"):
    require(forbidden not in all_java, f"forbidden migration/runtime token remains: {forbidden}")

for path in JAVA.rglob("*.java"):
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    require(len(lines) <= 420, f"Java responsibility exceeds 420 lines: {path.relative_to(ROOT)} ({len(lines)})")
    # Entity graphs may fetch one collection, but never multiple List bags.
    for graph in re.findall(r"@EntityGraph\(attributePaths\s*=\s*\{([^}]*)}\)", source):
        collection_paths = [value for value in re.findall(r'"([^"]+)"', graph) if value.endswith("Preferences")]
        require(len(collection_paths) <= 1, f"multiple bag fetch in {path.relative_to(ROOT)}")

# Known high-volume reads must remain batched rather than issue a query per row.
squad = (JAVA / "eu/royalblackwater/api/squads/SquadService.java").read_text(encoding="utf-8")
require("where sm.squad_id in (:ids)" in squad, "squad member list is not batch-loaded")
guide = (JAVA / "eu/royalblackwater/api/onboarding/NewcomerGuideService.java").read_text(encoding="utf-8")
require("where r.block_id in (:ids)" in guide, "newcomer guide resources are not batch-loaded")
ships = (JAVA / "eu/royalblackwater/api/ships/ShipQueryService.java").read_text(encoding="utf-8")
require("group by m.ship_id" in ships.lower(), "ship weapon mounts are not aggregated in one query")
masterdata = (JAVA / "eu/royalblackwater/api/masterdata/MasterDataQueryService.java").read_text(encoding="utf-8")
for marker in ("where m.ship_id in (:ids)", "where value.ship_id in (:ids)", "where ship_id in (:ids)"):
    require(marker in masterdata, f"master-data ship relation is not batch-loaded: {marker}")
references = (JAVA / "eu/royalblackwater/api/account/UserReferenceService.java").read_text(encoding="utf-8")
require("where u.id in (:ids)" in references, "user references are not batch-loaded")
guides = (JAVA / "eu/royalblackwater/api/guides/GuideService.java").read_text(encoding="utf-8")
require("builds.getMany" in guides and "for (Long buildId : normalizedBuildIds) builds.get" not in guides,
        "guide build references are not batch-loaded")
build_assembler = (JAVA / "eu/royalblackwater/api/builds/BuildAssembler.java").read_text(encoding="utf-8")
require("RuntimeCache cache" in build_assembler and "cache.options.computeIfAbsent" in build_assembler,
        "build list runtime catalogs are not request-cached")

print(f"Spring backend audit OK ({len(ops)} operations, {len(list(JAVA.rglob('*.java')))} Java files).")
