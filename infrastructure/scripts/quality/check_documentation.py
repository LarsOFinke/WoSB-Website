#!/usr/bin/env python3
"""Validate stable local references and module coverage in repository docs."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[3]
LINK_PATTERN = re.compile(r"!?\[[^]]*]\(([^)]+)\)")
FORBIDDEN_COMMANDS = {
    "python infrastructure/scripts/": "use python3 for repository scripts",
    "run_browser_smoke.py": "use frontend npm run test:browser",
}


MODULE_CATALOG = ROOT / "docs/architecture/MODULE_CATALOG.md"
MODULE_CACHE = ROOT / ".agents/MODULE_CACHE.md"
DEBUGGING_CACHE = ROOT / ".agents/DEBUGGING_CACHE.md"


def repository_markdown_files() -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z", "--cached", "--others",
         "--exclude-standard", "--", "*.md"],
        check=True,
        capture_output=True,
        text=True,
    )
    return sorted({ROOT / value for value in result.stdout.split("\0") if value})


def module_paths() -> list[str]:
    roots = (
        (
            ROOT / "spring-api/src/main/java/eu/royalblackwater/api",
            "spring-api/src/main/java/eu/royalblackwater/api",
        ),
        (ROOT / "frontend/src/modules", "frontend/src/modules"),
        (ROOT / "infrastructure/scripts", "infrastructure/scripts"),
    )
    paths: list[str] = []
    for root, relative in roots:
        paths.extend(
            f"{relative}/{path.name}/"
            for path in root.iterdir()
            if path.is_dir() and not path.name.startswith((".", "__"))
        )
    return sorted(paths)


def cache_failures() -> list[str]:
    failures: list[str] = []
    required = (MODULE_CATALOG, MODULE_CACHE, DEBUGGING_CACHE)
    for path in required:
        if not path.is_file():
            failures.append(f"missing agent documentation {path.relative_to(ROOT)}")
    if failures:
        return failures
    catalog = MODULE_CATALOG.read_text(encoding="utf-8")
    cache = MODULE_CACHE.read_text(encoding="utf-8")
    for module in module_paths():
        marker = f"`{module}`"
        if marker not in catalog:
            failures.append(f"docs/architecture/MODULE_CATALOG.md: missing module {module}")
        if marker not in cache:
            failures.append(f".agents/MODULE_CACHE.md: missing module {module}")
    return failures


def local_link_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split(maxsplit=1)[0]
    target = unquote(target.split("#", 1)[0])
    if not target or target.startswith(("http://", "https://", "mailto:", "/")):
        return None
    return target


def main() -> None:
    failures = cache_failures()
    if sys.argv[1:] == ["--cache-only"]:
        if failures:
            raise SystemExit("[agent-cache] " + "\n[agent-cache] ".join(failures))
        print(f"[agent-cache] OK: {len(module_paths())} module entries")
        return
    if sys.argv[1:]:
        raise SystemExit("Usage: check_documentation.py [--cache-only]")
    markdown_files = repository_markdown_files()
    for path in markdown_files:
        content = path.read_text(encoding="utf-8")
        for raw_target in LINK_PATTERN.findall(content):
            target = local_link_target(raw_target)
            if target and not (path.parent / target).resolve().exists():
                failures.append(f"{path.relative_to(ROOT)}: missing local link {target}")
        for token, guidance in FORBIDDEN_COMMANDS.items():
            if token in content:
                failures.append(f"{path.relative_to(ROOT)}: {token!r} is stale; {guidance}")
    if failures:
        raise SystemExit("[documentation] " + "\n[documentation] ".join(failures))
    print(f"[documentation] OK: {len(markdown_files)} repository Markdown files")


if __name__ == "__main__":
    main()
