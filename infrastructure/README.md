# Infrastructure

The infrastructure directory contains the Docker Compose deployment for PostgreSQL, the FastAPI backend, the NGINX frontend/TLS gateway and optional Uptime Kuma monitoring.

Direct Discord channel webhooks are delivered by the API container over its outbound network.

See `ARCHITECTURE.md`, `docs/OPERATIONS.md` and the scripts under `scripts/` for setup, updates, backups, restores and health checks.
