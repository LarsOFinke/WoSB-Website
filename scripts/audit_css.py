#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CSS_ROOT = ROOT / "frontend/src"
GLOBAL_ROOT = CSS_ROOT / "styles/global"
EXPECTED_GLOBAL_LAYERS = (
    "00-tokens.css",
    "10-foundation.css",
    "20-layout.css",
    "30-shell.css",
    "40-navigation-and-portal.css",
    "50-domain-workspaces.css",
    "60-operations.css",
    "70-integrations.css",
)


def fail(message: str) -> None:
    print(f"[css-audit] {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    css_files = sorted(CSS_ROOT.rglob("*.css"))
    if not css_files:
        fail("no CSS files found")

    manifest = (GLOBAL_ROOT / "index.js").read_text(encoding="utf-8")
    actual_layers = tuple(re.findall(r"import './(\d{2}-[^']+\.css)'", manifest))
    if actual_layers != EXPECTED_GLOBAL_LAYERS:
        fail(f"global layer order changed: {actual_layers!r}")

    sources = {path: path.read_text(encoding="utf-8") for path in css_files}
    combined = "\n".join(sources.values())
    definitions = set(re.findall(r"(--[a-zA-Z0-9_-]+)\s*:", combined))
    unresolved_without_fallback: Counter[str] = Counter()
    for match in re.finditer(r"var\(\s*(--[a-zA-Z0-9_-]+)([^)]*)\)", combined):
        name, suffix = match.groups()
        if name not in definitions and "," not in suffix:
            unresolved_without_fallback[name] += 1

    if unresolved_without_fallback:
        fail(f"undefined custom properties without fallback: {dict(unresolved_without_fallback)}")

    for path, source in sources.items():
        relative = path.relative_to(ROOT)
        if "@import" in source:
            fail(f"CSS @import is forbidden: {relative}")
        if ";base64," in source:
            fail(f"embedded base64 asset found: {relative}")
        if path.parent != GLOBAL_ROOT and re.search(r"(?m)^:root\s*\{", source):
            fail(f"feature stylesheet defines global tokens: {relative}")

    total_bytes = sum(path.stat().st_size for path in css_files)
    total_lines = sum(len(source.splitlines()) for source in sources.values())
    important_count = sum(source.count("!important") for source in sources.values())
    if important_count > 28:
        fail(f"!important budget exceeded: {important_count} > 28")

    print(f"[css-audit] files={len(css_files)} bytes={total_bytes} lines={total_lines} important={important_count}")
    for path in sorted(css_files, key=lambda item: item.stat().st_size, reverse=True):
        source = sources[path]
        print(
            f"[css-audit] {path.relative_to(ROOT)}: "
            f"{path.stat().st_size} bytes, {len(source.splitlines())} lines, "
            f"{source.count('!important')} important"
        )


if __name__ == "__main__":
    main()
