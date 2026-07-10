# Release 0.15.3 — Database-safe updates and monitoring recovery

## Update contract

`sudo ./update.sh` is now a code-only deployment by default. It rebuilds and
recreates the FastAPI and frontend gateway containers with `--no-deps`, leaving
PostgreSQL and its bind-mounted data directory untouched.

Database writes are opt-in:

- `--migrate` runs Alembic intentionally;
- changed files under `backend/migrations/versions/` trigger migrations
  automatically after a Git pull;
- `--seed` runs the idempotent seed intentionally;
- `--no-auto-migrate` forces a strictly code-only deployment.

The Staff Panel update button uses the same code-first runner. It never requests
a seed.

## Monitoring resilience

Uptime Kuma and `monitoring-gateway` are ensured before optional database work
and again after the application rollout. Failed seed or migration operations can
no longer prevent the monitoring stack from being started.
