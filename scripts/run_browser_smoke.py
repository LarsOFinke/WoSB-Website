#!/usr/bin/env python3
"""Run a small full-stack Chromium smoke test against disposable local data."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:5173"
ADMIN_USERNAME = "browser-smoke-admin"
ADMIN_PASSWORD = "BrowserSmokeAdmin-2026!"
MEMBER_USERNAME = "browser-smoke-member"
MEMBER_PASSWORD = "BrowserSmokeMember-2026!"
RESPONSIVE_VIEWPORTS = (
    {"width": 320, "height": 568},
    {"width": 375, "height": 667},
    {"width": 430, "height": 932},
    {"width": 720, "height": 900},
    {"width": 768, "height": 1024},
    {"width": 1024, "height": 768},
    {"width": 1440, "height": 900},
)


def wait_for_url(url: str, process: subprocess.Popen[str], timeout: float = 90) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Process exited before {url} became ready (exit {process.returncode}).")
        try:
            with urlopen(url, timeout=2) as response:
                if response.status < 500:
                    return
        except Exception:
            time.sleep(0.4)
    raise RuntimeError(f"Timed out waiting for {url}.")


def terminate(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def login(page: Page, username: str, password: str) -> None:
    page.goto(f"{FRONTEND_URL}/login")
    page.locator('input[autocomplete="username"]').fill(username)
    page.locator('input[autocomplete="current-password"]').fill(password)
    page.locator('button[type="submit"]').click()
    page.wait_for_url("**/profile")


def assert_responsive_layout(page: Page, paths: tuple[str, ...]) -> None:
    """Reject root-level clipping at the viewports covered by the design contract."""
    for viewport in RESPONSIVE_VIEWPORTS:
        page.set_viewport_size(viewport)
        for path in paths:
            page.goto(f"{FRONTEND_URL}{path}", wait_until="domcontentloaded")
            page.locator("#app").wait_for()
            overflow = page.evaluate(
                """
                () => {
                  const root = document.documentElement
                  const excess = root.scrollWidth - root.clientWidth
                  if (excess <= 1) return null
                  const offenders = [...document.querySelectorAll('body *')]
                    .filter((element) => {
                      const style = getComputedStyle(element)
                      if (style.position === 'fixed' || style.position === 'absolute') return false
                      const box = element.getBoundingClientRect()
                      return box.right > root.clientWidth + 1 || box.left < -1
                    })
                    .slice(0, 5)
                    .map((element) => ({
                      tag: element.tagName.toLowerCase(),
                      className: String(element.className || ''),
                      right: Math.round(element.getBoundingClientRect().right),
                    }))
                  return { excess, offenders }
                }
                """
            )
            assert overflow is None, (
                f"Horizontal overflow at {viewport['width']}x{viewport['height']} on {path}: "
                f"{json.dumps(overflow, ensure_ascii=False)}"
            )


def run_smoke() -> None:
    with tempfile.TemporaryDirectory(prefix="rbf-browser-smoke-") as raw_temp:
        temp = Path(raw_temp)
        env_file = temp / "backend.env"
        env_file.write_text(
            "\n".join(
                [
                    "APP_ENV=development",
                    f"DATABASE_URL=sqlite:///{(temp / 'smoke.db').as_posix()}",
                    "DB_SCHEMA_MODE=create",
                    f"UPLOAD_DIR={(temp / 'uploads').as_posix()}",
                    f"CONTROL_REQUEST_DIR={(temp / 'control/inbox').as_posix()}",
                    f"CONTROL_STATUS_DIR={(temp / 'control/status').as_posix()}",
                    f"CORS_ORIGINS={FRONTEND_URL}",
                    "SESSION_COOKIE_SECURE=false",
                    "AUTO_SEED=true",
                    f"SEED_ADMIN_USERNAME={ADMIN_USERNAME}",
                    f"SEED_ADMIN_PASSWORD={ADMIN_PASSWORD}",
                    "SEED_ADMIN_DISPLAY_NAME=Browser Smoke Admin",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        backend_log = (temp / "backend.log").open("w+", encoding="utf-8")
        frontend_log = (temp / "frontend.log").open("w+", encoding="utf-8")
        env = os.environ.copy()
        env["RBF_ENV_FILE"] = str(env_file)
        env["PYTHONPATH"] = str(BACKEND / "src")
        backend_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=BACKEND,
            env=env,
            stdout=backend_log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        frontend_process: subprocess.Popen[str] | None = None
        try:
            wait_for_url(f"{BACKEND_URL}/api/health", backend_process)
            frontend_process = subprocess.Popen(
                ["npm", "run", "dev:default", "--", "--host", "127.0.0.1"],
                cwd=FRONTEND,
                env=os.environ.copy(),
                stdout=frontend_log,
                stderr=subprocess.STDOUT,
                text=True,
            )
            wait_for_url(FRONTEND_URL, frontend_process)

            with sync_playwright() as playwright:
                executable = os.environ.get("RBF_CHROMIUM_EXECUTABLE") or shutil.which("chromium")
                launch_args = {"headless": True}
                if executable:
                    launch_args["executable_path"] = executable
                browser = playwright.chromium.launch(**launch_args)
                context = browser.new_context(base_url=FRONTEND_URL)
                page = context.new_page()

                assert_responsive_layout(page, ("/", "/builds", "/guides", "/login", "/register"))

                page.goto(f"{FRONTEND_URL}/register")
                page.locator('input[autocomplete="username"]').fill(MEMBER_USERNAME)
                page.locator('input[autocomplete="nickname"]').fill("Browser Smoke Member")
                page.locator('input[autocomplete="new-password"]').fill(MEMBER_PASSWORD)
                page.locator('button[type="submit"]').click()
                page.locator(".registration-review-panel").wait_for()

                login(page, ADMIN_USERNAME, ADMIN_PASSWORD)
                assert_responsive_layout(
                    page,
                    ("/admin", "/admin/discord-webhooks", "/admin/database-backups"),
                )
                status_response = context.request.get(f"{FRONTEND_URL}/api/admin/system/update")
                assert status_response.ok, status_response.text()
                status_payload = status_response.json()
                forbidden_status_keys = {"requested_by", "current_commit", "available_commit", "log_tail"}
                assert forbidden_status_keys.isdisjoint(status_payload), json.dumps(status_payload, indent=2)

                requests_response = context.request.get(
                    f"{FRONTEND_URL}/api/admin/registration-requests?status=pending"
                )
                assert requests_response.ok, requests_response.text()
                pending = requests_response.json()
                request_row = next(row for row in pending if row["username"] == MEMBER_USERNAME)
                approve_response = context.request.post(
                    f"{FRONTEND_URL}/api/admin/registration-requests/{request_row['id']}/approve",
                    data={"note": "Browser smoke approval"},
                )
                assert approve_response.ok, approve_response.text()
                logout_response = context.request.post(f"{FRONTEND_URL}/api/auth/logout")
                assert logout_response.ok, logout_response.text()

                login(page, MEMBER_USERNAME, MEMBER_PASSWORD)
                assert_responsive_layout(page, ("/profile", "/builds", "/guides", "/calendar"))
                page.goto(f"{FRONTEND_URL}/builds")
                page.locator("#builds-title").wait_for()
                build_response = context.request.get(f"{FRONTEND_URL}/api/builds?limit=1&offset=0")
                assert build_response.ok, build_response.text()
                build_page = build_response.json()
                assert {"items", "total", "limit", "offset"}.issubset(build_page)
                assert build_page["limit"] == 1

                browser.close()
        except Exception:
            backend_log.flush()
            frontend_log.flush()
            backend_log.seek(0)
            frontend_log.seek(0)
            print("\n--- backend smoke log ---", file=sys.stderr)
            print(backend_log.read(), file=sys.stderr)
            print("\n--- frontend smoke log ---", file=sys.stderr)
            print(frontend_log.read(), file=sys.stderr)
            raise
        finally:
            if frontend_process is not None:
                terminate(frontend_process)
            terminate(backend_process)
            backend_log.close()
            frontend_log.close()


if __name__ == "__main__":
    run_smoke()
    print("Full-stack browser smoke test passed.")
