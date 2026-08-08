# Infrastructure Scripts

The scripts are organized by operational boundaries. Entry points remain stable; internal helpers
are not invoked directly from systemd or CI.

## Entry Points

- `../../deploy.sh --configure` configures the test server; test is the default.
- `../../deploy.sh --production --configure` explicitly configures production.
- `../../deploy.sh` and `../../update.sh` delegate to `release/deploy-from-origin.sh`;
  production requires `--production` on every run.
- `diagnostics/debug.sh` follows the same target selection and collects bounded, redacted target-system diagnostics only at the origin.
- `../setup.sh` delegates internally to `setup/` and is invoked only by local development and artifact workflows.
- `release/build-artifact.sh` builds and validates the compiled deployment artifact.
- `services/boot.sh`, `services/start.sh`, `services/stop.sh`, and `services/systemd-stop.sh` form the container lifecycle.

## Areas

- `backup/`: consistent backups, restores, recovery bundles, and the admin runner. The `backup_runner_*.py` files are import modules of `backup-admin-runner.py`, even though they do not appear as shell callers.
- `checks/`: preflight, host-security, smoke, and diagnostic checks.
- `deployment/`: systemd installation.
- `diagnostics/`: origin collector, ephemeral remote collector, and local redaction for agent-friendly operational diagnostics.
- `generation/`: deterministic API, Java, Flyway, Build, and documentation generators. Published Flyway files remain immutable despite the relocated generator.
- `lib/`: shared shell libraries for Docker, environment, host, storage, TLS, JSON, and maintenance status.
- `quality/`: repository audits, hygiene, security checks, and the complete validation gate; focused contract checks live in `quality/tests/`.
- `release/`: artifact build and verification, packaging, origin transfer, installation, rollback, and TLS/host preparation.
- `services/`: running application operations and controlled admin actions.
- `setup/`: CLI options and setup orchestration.
- `tls/`: certificate renewal and synchronization.

## Placement and Ownership Rule

Only the public operating contracts `deploy.sh` and `update.sh` remain at the repository root.
All shared scripts live in this tree and are assigned to a module by responsibility; a new top-level
`scripts/` directory is not allowed. `.agents/scripts/` and `frontend/scripts/` are tightly bound
to their owner modules and are not general script collections.

Shared placement does not mean every module is part of production.
`release/package_deployment_artifact.py` uses an explicit runtime allowlist. `quality/`,
`generation/`, and the packaging programs themselves remain at the origin or in CI and are not shipped.

## Cleanup Review (2026-08-04)

- All versioned shell scripts pass `bash -n`.
- All versioned Python scripts pass `python3 -m compileall`.
- Public wrappers (`deploy.sh`, `update.sh`) were not merged because they represent existing operational contracts.
- Manual recovery helpers (`merge-encryption-keyring.sh`, `verify-recovery.sh`) were not deleted: missing source-code references are not evidence of non-use for deliberately manual emergency tools.
- `release/package_release.py` remains because the release workflow still invokes it for the additional source archive.
