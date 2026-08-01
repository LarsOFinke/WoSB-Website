#!/usr/bin/env python3
"""Deterministic repository security invariants.

This complements online software-composition analysis. It intentionally checks
security properties that are specific to this repository and can run offline.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAILURES: list[str] = []
CHECKS = 0


def check(condition: bool, message: str) -> None:
    global CHECKS
    CHECKS += 1
    if not condition:
        FAILURES.append(message)


def text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


# CI supply-chain hygiene. All external actions are pinned to reviewed immutable commits.
workflow_paths = sorted((ROOT / ".github/workflows").glob("*.yml"))
workflow_sources = "\n".join(path.read_text(encoding="utf-8") for path in workflow_paths)
check("pull_request_target:" not in workflow_sources, "pull_request_target must not be used")
approved_actions = {
    "actions/checkout": "d23441a48e516b6c34aea4fa41551a30e30af803",
    "actions/setup-python": "ece7cb06caefa5fff74198d8649806c4678c61a1",
    "actions/setup-node": "249970729cb0ef3589644e2896645e5dc5ba9c38",
    "actions/upload-artifact": "b7c566a772e6b6bfb58ed0dc250532a479d7789f",
    "google/osv-scanner-action/.github/workflows/osv-scanner-reusable-pr.yml": (
        "3adb4b14a2b0623876d18d863a498b785fb3752d"
    ),
    "google/osv-scanner-action/.github/workflows/osv-scanner-reusable.yml": (
        "3adb4b14a2b0623876d18d863a498b785fb3752d"
    ),
}
action_references = 0
for path in workflow_paths:
    source = path.read_text(encoding="utf-8")
    checkout_count = source.count("actions/checkout@")
    check(
        source.count("persist-credentials: false") >= checkout_count,
        f"{path.relative_to(ROOT)} must disable persisted checkout credentials",
    )
    for line_number, line in enumerate(source.splitlines(), start=1):
        match = re.match(r'\s*(?:-\s*)?uses:\s*["\']?([^@\s"\']+)@([^\s"\']+)', line)
        if match is None:
            continue
        action, revision = match.groups()
        if action.startswith(("./", "docker://")):
            continue
        action_references += 1
        check(
            action in approved_actions,
            f"unreviewed action in {path.relative_to(ROOT)}:{line_number}",
        )
        if action in approved_actions:
            check(
                revision == approved_actions[action],
                f"mutable or unexpected action revision in {path.relative_to(ROOT)}:{line_number}",
            )
check(action_references > 0, "no external GitHub Actions were inspected")
check("osv-scanner-reusable" in workflow_sources, "OSV dependency scanning workflow is missing")

# Container and edge hardening.
compose = text("infrastructure/compose.yml")
check("privileged: true" not in compose, "privileged container found")
check("/var/run/docker.sock" not in compose, "Docker socket must not be mounted")
check(compose.count("no-new-privileges:true") >= 7, "services must retain no-new-privileges")
headers = text("infrastructure/nginx/security-headers.conf")
for header in (
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "Cross-Origin-Opener-Policy",
    "Cross-Origin-Resource-Policy",
    "X-Permitted-Cross-Domain-Policies",
):
    check(header in headers, f"missing edge header: {header}")
upload_headers = text("infrastructure/nginx/upload-security-headers.conf")
for header in (
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "Content-Security-Policy",
    "Cross-Origin-Resource-Policy",
):
    check(header in upload_headers, f"missing upload response header: {header}")
nginx = text("infrastructure/nginx/default.conf")
check("limit_req zone=auth_login" in nginx, "login rate limit is missing")
check("limit_req zone=auth_register" in nginx, "registration rate limit is missing")
session_config = text("backend/config/session.cfg")
check(
    "cookie_samesite = lax" in session_config
    or "cookie_samesite = strict" in session_config,
    "session cookie SameSite protection is missing",
)
auth_routes = text("backend/src/app/modules/accounts/routes/auth.py")
check("httponly=True" in auth_routes, "session cookie must remain HttpOnly")

# Secret handling and Discord webhook invariants.
webhook_model = text("backend/src/app/modules/admin/models/outbound_webhook.py")
webhook_service = text("backend/src/app/modules/admin/services/outbound_webhook_service.py")
secret_box = text("backend/src/app/core/secret_box.py")
check("discord_avatar_url" not in webhook_model, "obsolete webhook avatar column remains")
check("webhook_secret_box.encrypt" in webhook_service, "webhook endpoints are not encrypted")
check(
    "MultiFernet" in secret_box and "needs_rotation" in secret_box,
    "key rotation support missing",
)
check(
    "WEBHOOK_ENCRYPTION_KEYS" in text("infrastructure/scripts/lib/env.sh"),
    "deployment does not generate a webhook encryption key",
)

# High-confidence committed-secret patterns in production/configuration files.
scan_roots = [
    ROOT / "backend/src",
    ROOT / "frontend/src",
    ROOT / "infrastructure",
    ROOT / "tools/recovery-tool",
    ROOT / ".github",
]
secret_patterns = {
    "private key": re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]{64,}"
        r"-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    ),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    "Discord webhook credential": re.compile(
        r"https://(?:canary\.|ptb\.)?discord(?:app)?\.com/api(?:/v\d+)?/webhooks/"
        r"\d{10,}/[A-Za-z0-9._-]{30,}"
    ),
}
text_suffixes = {
    ".py", ".js", ".mjs", ".vue", ".sh", ".yml", ".yaml", ".conf", ".env",
    ".example", ".ini", ".cfg", ".toml", ".json", ".md", ".txt", ".pem", ".key",
}
for root in scan_roots:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        is_candidate = (
            path.suffix.casefold() in text_suffixes
            or path.name.startswith(".env")
            or path.name.startswith("Dockerfile")
        )
        if not is_candidate or path.stat().st_size > 2_000_000:
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        for label, pattern in secret_patterns.items():
            check(
                pattern.search(source) is None,
                f"possible committed {label}: {path.relative_to(ROOT)}",
            )

backup_admin_runner = text("infrastructure/scripts/backup/backup-admin-runner.py")
restore_runner_block = backup_admin_runner.split("def restore_postgresql", 1)[1].split("@staticmethod", 1)[0]
check(
    restore_runner_block.index("consume_database_restore_approval")
    < restore_runner_block.index("resolve_local_postgres_backup"),
    "database restore host approval must precede local backup resolution",
)

# Frozen recovery client must retain explicit host-key pinning and secret-minimal profiles.
recovery_sftp = text("tools/recovery-tool/src/rbf_recovery_tool/sftp_client.py")
recovery_config = text("tools/recovery-tool/src/rbf_recovery_tool/config.py")
recovery_verification = text("tools/recovery-tool/src/rbf_recovery_tool/verification.py")
recovery_lab = text("tools/recovery-tool/src/rbf_recovery_tool/docker_lab.py")
recovery_linux_setup = text("tools/recovery-tool/src/rbf_recovery_tool/linux_setup.py")
check("PinnedFingerprintPolicy" in recovery_sftp, "recovery client lost SSH host-key pinning")
check("AutoAddPolicy" not in recovery_sftp, "recovery client must not auto-trust SSH host keys")
check("password:" not in recovery_config, "recovery profile must not persist passwords")
check("verify_sidecar" in recovery_verification, "recovery client must verify transport checksums")
check("_validated_members" in recovery_verification, "recovery client must validate archive members")
check(
    '127.0.0.1:${{POSTGRES_LOCAL_PORT}}:5432' in recovery_lab,
    "local recovery database must remain loopback-only",
)
preflight_override = recovery_lab.split("def _application_preflight_override", 1)[1].split("def verify_recovery", 1)[0]
check("networks: [rbf_recovery_backend]" in preflight_override, "recovery API preflight must use the internal lab network")
check("ports:" not in preflight_override, "recovery API preflight must not publish host ports")
check("no-new-privileges:true" in recovery_lab, "local recovery database must prevent privilege escalation")
check("${{POSTGRES_PASSWORD}}" in recovery_lab, "local recovery compose must reference the protected env file for its password")
check("require_root_owned=True" in recovery_linux_setup, "privileged recovery helper must be root-owned")
check("shell=True" not in recovery_linux_setup, "Linux recovery setup must not invoke a shell")

# Python code: no dynamic execution or shell=True in production/runtime modules.
python_sources = [
    *(ROOT / "backend/src").rglob("*.py"),
    *(ROOT / "infrastructure/scripts").rglob("*.py"),
    *(ROOT / "tools/recovery-tool/src").rglob("*.py"),
]
for path in python_sources:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        FAILURES.append(f"cannot parse {path.relative_to(ROOT)}: {exc}")
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            check(
                node.func.id not in {"eval", "exec"},
                f"dynamic execution in {path.relative_to(ROOT)}",
            )
        if isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant):
                    check(
                        keyword.value.value is not True,
                        f"shell=True in {path.relative_to(ROOT)}",
                    )

if FAILURES:
    print("[security-audit] FAILED")
    for failure in FAILURES:
        print(f" - {failure}")
    raise SystemExit(1)

print(f"[security-audit] {CHECKS} offline security invariants passed")
