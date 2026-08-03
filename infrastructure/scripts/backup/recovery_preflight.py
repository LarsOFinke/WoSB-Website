#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_ROOT = os.environ.get("RBF_ARTIFACT_ROOT")
IMPORT_ROOT = Path(ARTIFACT_ROOT) if ARTIFACT_ROOT else REPO_ROOT
if str(IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(IMPORT_ROOT))

from contracts.recovery.contract import (  # noqa: E402
    MigrationGraph,
    add_report_check,
    assess_compatibility,
    descriptor_from_manifest,
    finalize_report,
    is_production_consistent,
    new_report,
    write_report,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--metadata", type=Path)
    source.add_argument("--manifest", type=Path)
    parser.add_argument("--migrations-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--allow-unrecorded", action="store_true")
    parser.add_argument("--allow-uncoordinated", action="store_true")
    args = parser.parse_args()

    source_path = args.metadata or args.manifest
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("Recovery manifest must contain a JSON object.")
    descriptor = descriptor_from_manifest(payload)
    graph = MigrationGraph.from_directory(args.migrations_dir)
    assessment = assess_compatibility(
        descriptor,
        graph,
        allow_unrecorded=args.allow_unrecorded,
    )
    consistent = is_production_consistent(descriptor)
    accepted = assessment.compatible and (consistent or args.allow_uncoordinated)
    result = {
        "descriptor": descriptor.to_dict(),
        "assessment": assessment.to_dict(),
        "production_consistent": consistent,
        "accepted": accepted,
    }
    if args.report:
        report = new_report(
            mode="compatibility-preflight",
            source=str(source_path),
            descriptor=descriptor,
        )
        add_report_check(
            report,
            name="metadata_compatibility",
            status="passed" if accepted else "failed",
            detail=assessment.detail,
            data=result,
        )
        add_report_check(
            report,
            name="runtime_recovery",
            status="skipped",
            detail="Compatibility-only checks never prove runtime recoverability.",
        )
        finalize_report(report, status="passed" if accepted else "failed", recoverable=False)
        write_report(args.report, report)
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if accepted else 2)


if __name__ == "__main__":
    main()
