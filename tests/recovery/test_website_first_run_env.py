from pathlib import Path
import os
import shutil
import subprocess


def test_first_run_preserves_defaults_and_requested_test_hostname(tmp_path):
    root = Path(__file__).parents[2]
    infra = tmp_path / "runtime"
    infra.mkdir()
    shutil.copyfile(root / "infrastructure/.env.example", infra / ".env.example")
    target = tmp_path / "shared/website.env"
    credentials = tmp_path / "shared/credentials.txt"
    script = root / "infrastructure/scripts/release/prepare-website-env.sh"
    command = ["bash", str(script), str(target), str(credentials), "test",
               "fleet.example.test", "127.0.0.1", "", "ssh.example.test", "22"]
    environment = {**os.environ, "RBF_RUNTIME_INFRA_DIR": str(infra)}
    subprocess.run(command, env=environment, check=True, capture_output=True, text=True)
    values = dict(line.split("=", 1) for line in target.read_text().splitlines()
                  if line and not line.startswith("#") and "=" in line)
    assert values["APP_HOSTNAME"] == "fleet.example.test"
    assert values["CORS_ORIGINS"] == "http://fleet.example.test"
    assert values["COMPOSE_PROJECT_NAME"] == "rbf-hub"
    assert values["FLYWAY_BASELINE_ON_MIGRATE"] == "false"
    assert values["RBF_LOOPBACK_PORT"] == "18080"
    assert values["SESSION_COOKIE_SECURE"] == "false"
    assert values["POSTGRES_PASSWORD"] and "CHANGE_ME" not in values["POSTGRES_PASSWORD"]
    assert target.stat().st_mode & 0o777 == 0o600
    initial = credentials.read_bytes()
    subprocess.run(command, env=environment, check=True, capture_output=True, text=True)
    assert credentials.read_bytes() == initial
    assert f"POSTGRES_PASSWORD={values['POSTGRES_PASSWORD']}" in target.read_text()
