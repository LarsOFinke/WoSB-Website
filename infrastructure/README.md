# Infrastructure

This directory contains the Spring-only Compose runtime, TLS/NGINX configuration, host-control runners, and release, update, backup, and restore scripts.

The two deployment entry points intentionally live at repository level:
`../deploy.sh` transfers the verified release artifact; the internal
`scripts/release/setup_website.sh` installs it on the target host.
`scripts/release/` contains the internal release implementations, the artifact verifier,
and release rollback. Origin transfer runs through `../deploy.sh`, updates through
`../update.sh`; both target the test server when no flag is provided. Production is selected
only with `--production`. `scripts/diagnostics/debug.sh` uses the same target selection for
read-only, bounded, locally redacted diagnostics. The separate private origin configurations
are named `.env.origin.test` and `.env.origin.production`; the corresponding `.example` files
are templates. The target server uses the versioned runtime wrappers.

- `compose.yml`: source build for development and initial configuration.
- `compose.release.yml`: production from compiled JAR and frontend `dist`.
- `scripts/release/`: verified atomic artifact installation, rollback, and targeted cleanup of failed inactive releases.
- `scripts/backup/`: coordinated PostgreSQL/file/recovery backups.
- `scripts/migration/`: one-time fail-closed gate for existing databases.
- `scripts/diagnostics/`: origin collection, ephemeral remote collector, and redaction for agent-friendly diagnostic output.
- `scripts/quality/`: repository gates, audits, and focused script tests; not part of the runtime artifact.
- `scripts/generation/`: deterministic source and documentation generators; not part of the runtime artifact.

The Alpine-based API and gateway runtime images apply security updates from the pinned stable
Alpine branch during the build with `apk upgrade --no-cache`. The security workflow then scans
both finished images with Trivy and fails on fixable HIGH/CRITICAL findings.

Production releases live under `/srv/rbf/releases/<version>`, shared configuration and data under `/srv/rbf/shared`, and `/srv/rbf/current` atomically points to the active release.

After a failed attempt, the same version can be installed again without deleting backups or diagnostics:

```bash
sudo /srv/rbf/current/infrastructure/scripts/release/cleanup-failed-release.sh --version 1.0.0
```

The script refuses active releases and states other than `failed` and `activating`.
Use `--yes` to skip confirmation in automated workflows.
