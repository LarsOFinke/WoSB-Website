#!/usr/bin/env python3
"""Fail closed when an NVD-backed temporary suppression has a known fix."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_POLICY = ROOT / "spring-api/dependency-suppression-policy.json"
NVD_CVE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
MAVEN_CENTRAL_URL = "https://repo.maven.apache.org/maven2"


def version_key(value: str) -> tuple[tuple[int, object], ...]:
    """Compare the numeric release versions used by the current policies."""
    parts: list[tuple[int, object]] = []
    for token in re.findall(r"\d+|[A-Za-z]+", value):
        parts.append((0, int(token)) if token.isdigit() else (1, token.lower()))
    return tuple(parts)


def cpe_matches(entry: dict, vendor: str, product: str) -> bool:
    criteria = str(entry.get("criteria", ""))
    pieces = criteria.split(":")
    return len(pieces) > 4 and pieces[2] == "a" and pieces[3] == vendor and pieces[4] == product


def walk_cpe_matches(node: object):
    if isinstance(node, dict):
        for match in node.get("cpeMatch", []):
            if isinstance(match, dict):
                yield match
        for key, value in node.items():
            if key not in {"cpeMatch", "criteria"}:
                yield from walk_cpe_matches(value)
    elif isinstance(node, list):
        for child in node:
            yield from walk_cpe_matches(child)


def fixed_versions(cve: dict, vendor: str, product: str) -> set[str]:
    """Return fixes explicitly represented by NVD affected-version metadata."""
    versions: set[str] = set()
    for configuration in cve.get("configurations", []):
        for match in walk_cpe_matches(configuration):
            if not match.get("vulnerable", True) or not cpe_matches(match, vendor, product):
                continue
            if match.get("versionEndExcluding"):
                versions.add(str(match["versionEndExcluding"]))
            if match.get("versionEndIncluding"):
                versions.add(str(match["versionEndIncluding"]))

    for source in cve.get("affected", []):
        for product_data in source.get("product", source.get("affectedData", [])):
            if product_data.get("vendor") != vendor or product_data.get("product") != product:
                continue
            for affected_version in product_data.get("versions", []):
                if affected_version.get("status") == "fixed":
                    versions.add(str(affected_version.get("version")))
    return {version for version in versions if version and version.lower() not in {"none", "*"}}


def fetch_cve(cve_id: str, api_key: str | None = None) -> dict:
    query = urlencode({"cveId": cve_id})
    headers = {"User-Agent": "royal-blackwater-fleet-dependency-policy/1.0"}
    if api_key:
        headers["apiKey"] = api_key
    request = Request(f"{NVD_CVE_URL}?{query}", headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(f"NVD lookup failed for {cve_id}: {error}") from error


def maven_artifact_url(package_url: str, version: str, repository: str = MAVEN_CENTRAL_URL) -> str:
    match = re.fullmatch(r"pkg:maven/([^/@]+)/([^/@]+)@[^?]+", package_url)
    if not match:
        raise RuntimeError(f"unsupported Maven package URL: {package_url}")
    group, artifact = match.groups()
    group_path = group.replace(".", "/")
    return f"{repository.rstrip('/')}/{group_path}/{artifact}/{version}/{artifact}-{version}.pom"


def artifact_available(package_url: str, version: str, repository: str = MAVEN_CENTRAL_URL) -> bool:
    """Return whether a fixed Maven artifact can actually be fetched."""
    request = Request(maven_artifact_url(package_url, version, repository), method="HEAD")
    try:
        with urlopen(request, timeout=30):
            return True
    except HTTPError as error:
        if error.code == 404:
            return False
        raise RuntimeError(f"Maven artifact lookup failed ({error.code})") from error
    except (URLError, TimeoutError) as error:
        raise RuntimeError(f"Maven artifact lookup failed: {error}") from error


def validate_policy(policy: dict, api_key: str | None, fetch=fetch_cve,
                    available=artifact_available) -> list[str]:
    failures: list[str] = []
    for item in policy.get("policies", []):
        cve_id = item["cve"]
        if item.get("action") != "allow-unfixed-only":
            failures.append(f"{cve_id}: unsupported policy action")
            continue
        record = fetch(cve_id, api_key)
        vulnerabilities = record.get("vulnerabilities", [])
        if len(vulnerabilities) != 1:
            failures.append(f"{cve_id}: NVD returned {len(vulnerabilities)} records")
            continue
        cve = vulnerabilities[0].get("cve", {})
        fixes = fixed_versions(cve, item["vendor"], item["product"])
        current = version_key(item["current_version"])
        newer_fixes = sorted(fix for fix in fixes if version_key(fix) > current)
        if newer_fixes:
            package_url = item.get("package_url")
            availability = item.get("availability")
            if package_url and availability:
                repository = availability.get("repository", MAVEN_CENTRAL_URL)
                newer_fixes = [fix for fix in newer_fixes
                               if available(package_url, fix, repository)]
            if newer_fixes:
                label = "fetchable patched" if package_url and availability else "patched"
                failures.append(f"{cve_id}: NVD reports a {label} version ({', '.join(newer_fixes)})")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    args = parser.parse_args()
    try:
        policy = json.loads(args.policy.read_text(encoding="utf-8"))
        failures = validate_policy(policy, os.environ.get("NVD_API_KEY"))
    except (OSError, KeyError, json.JSONDecodeError, RuntimeError) as error:
        print(f"[dependency-policy] ERROR: {error}", file=sys.stderr)
        return 1
    if failures:
        for failure in failures:
            print(f"[dependency-policy] ERROR: {failure}", file=sys.stderr)
        return 1
    print(f"[dependency-policy] OK: {len(policy.get('policies', []))} NVD-backed suppression policies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
