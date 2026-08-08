#!/usr/bin/env python3
"""Assemble the generated OpenAPI compatibility artifact from focused source fragments."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "openapi/source"
TARGET = ROOT / "openapi/openapi.json"
METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}
SAFE_NAME = re.compile(r"[A-Za-z0-9_]+")


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exception:
        raise SystemExit(f"Invalid OpenAPI fragment {path.relative_to(ROOT)}: {exception}") from exception
    if not isinstance(value, dict):
        raise SystemExit(f"OpenAPI fragment must be an object: {path.relative_to(ROOT)}")
    return value


def assemble() -> dict:
    root = load_json(SOURCE / "root.json")
    if set(root) != {"openapi", "info"} or not isinstance(root["info"], dict):
        raise SystemExit("openapi/source/root.json must contain exactly openapi and info")

    schemas: dict[str, dict] = {}
    for path in sorted((SOURCE / "schemas").glob("*.json")):
        name = path.stem
        if SAFE_NAME.fullmatch(name) is None:
            raise SystemExit(f"Invalid schema fragment filename: {path.name}")
        if name in schemas:
            raise SystemExit(f"Duplicate OpenAPI schema: {name}")
        schemas[name] = load_json(path)
    if not schemas:
        raise SystemExit("OpenAPI source contains no schemas")

    paths: dict[str, dict] = {}
    operation_ids: set[str] = set()
    for source_path in sorted((SOURCE / "operations").glob("*.json")):
        fragment = load_json(source_path)
        if set(fragment) != {"path", "method", "operation"}:
            raise SystemExit(f"Operation fragment has unexpected keys: {source_path.relative_to(ROOT)}")
        api_path = fragment["path"]
        method = fragment["method"]
        operation = fragment["operation"]
        if not isinstance(api_path, str) or not api_path.startswith("/api/"):
            raise SystemExit(f"Invalid API path in {source_path.relative_to(ROOT)}")
        if method not in METHODS or not isinstance(operation, dict):
            raise SystemExit(f"Invalid method/operation in {source_path.relative_to(ROOT)}")
        operation_id = operation.get("operationId")
        if operation_id != source_path.stem:
            raise SystemExit(f"Operation filename must match operationId: {source_path.relative_to(ROOT)}")
        if operation_id in operation_ids:
            raise SystemExit(f"Duplicate operationId: {operation_id}")
        operation_ids.add(operation_id)
        path_item = paths.setdefault(api_path, {})
        if method in path_item:
            raise SystemExit(f"Duplicate operation: {method.upper()} {api_path}")
        path_item[method] = operation

    if not paths:
        raise SystemExit("OpenAPI source contains no operations")
    return {
        "components": {"schemas": dict(sorted(schemas.items()))},
        "info": root["info"],
        "openapi": root["openapi"],
        "paths": {path: paths[path] for path in sorted(paths)},
    }


def render() -> str:
    return json.dumps(assemble(), indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = render()
    if args.check:
        if not TARGET.is_file() or TARGET.read_text(encoding="utf-8") != content:
            raise SystemExit("openapi/openapi.json is stale; run assemble_openapi.py")
    else:
        TARGET.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
