# Infrastructure

The infrastructure directory contains the Docker Compose deployment for PostgreSQL, the FastAPI backend, the NGINX frontend/TLS gateway and optional Uptime Kuma monitoring.

Direct Discord channel webhooks are delivered by the API container over its outbound network.

See `docs/ARCHITECTURE.md`, `docs/OPERATIONS.md`, `docs/DISASTER_RECOVERY.md` and the scripts under `scripts/` for setup, updates, backups, restores and health checks.

## Admin-triggered remote and disaster-recovery backups

The admin backup page communicates only through protected control and status files. A root-owned
systemd path unit claims each request, creates the PostgreSQL and application-file artifacts,
and transfers them through strict-host-key SFTP. When age recovery is enabled, it also creates and
transfers the complete encrypted recovery bundle containing runtime configuration and secrets. Remote SSH credentials are stored below
`data/control/secrets/backup-remote/`, never in the database or frontend runtime. See
`docs/OPERATIONS.md` for setup and target-account requirements.
