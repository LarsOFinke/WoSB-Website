# Alpha infrastructure status

## Implemented

- Fresh Raspberry Pi/Debian bootstrap through `infrastructure/setup.sh`.
- Automatic Docker/Compose, Git, OpenSSL and UFW installation where supported by APT.
- Generated production secrets and first-run administrator credentials.
- Dual database lifecycle:
  - SQLite plus automatic schema creation for local development;
  - PostgreSQL plus Alembic migrations for production.
- Deterministic deployment controller:
  1. start and verify PostgreSQL;
  2. run Alembic migrations;
  3. run idempotent seed data;
  4. start and verify FastAPI;
  5. start NGINX and optional Uptime Kuma.
- Vue production build served by NGINX.
- Self-signed HTTPS on the first LAN boot.
- Internal-only API network and loopback-only PostgreSQL/monitoring ports.
- systemd boot service and daily local backup timer.
- PostgreSQL dump, file backup and restore scripts.
- Readiness checks, smoke test, source validation and GitHub Actions CI.

## Validated in the development environment

- Backend unit and access-policy tests.
- SQLite migration lifecycle and Alembic schema-diff check.
- PostgreSQL migration SQL rendering.
- Frontend localization validation and production build.
- Shell syntax, Compose model structure and deployment-order assertions.
- Simulated fresh first run, including secret generation, file permissions and TLS SAN values.

## Requires validation on the target Pi

- Real ARM64 Docker image builds.
- Real PostgreSQL container startup and migration execution.
- Host firewall behavior with the Pi's existing SSH configuration.
- systemd boot and backup timer after a reboot.
- LAN DNS/mDNS behavior for the selected hostname.

## Before public internet exposure

- Replace the generated certificate with a trusted ACME/Let's Encrypt certificate.
- Add encrypted off-host backups and restore drills.
- Review SSH access, user accounts and network segmentation.
- Add edge rate limiting, alerting and container/image vulnerability scanning.
- Define an upgrade and rollback policy for tagged releases.
