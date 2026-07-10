# Server updates and Staff Panel operations

`setup.sh` and `update.sh` have separate responsibilities.

## First installation or infrastructure changes

Use `setup.sh` when the host, domain, TLS, firewall, systemd units or generated
secrets need to be provisioned or changed:

```bash
sudo ./setup.sh \
  --profile full \
  --domain royal-blackwater-fleet.eu \
  --tls-mode auto \
  --letsencrypt-email you@example.com
```

## Normal application update

A normal update changes only the API and frontend gateway:

```bash
sudo ./update.sh
```

The default update runner:

1. refuses to overwrite tracked local source changes;
2. performs a fast-forward-only Git update;
3. creates a file backup without connecting to PostgreSQL;
4. rebuilds the API and frontend gateway images;
5. keeps PostgreSQL, its container and its data directory unchanged;
6. recreates only the API and frontend gateway (`--no-deps`);
7. ensures Uptime Kuma and its HTTPS gateway are running;
8. runs application and monitoring smoke tests.

The PostgreSQL data remains in `infrastructure/data/postgres`. The update path
never removes that directory, never runs `docker compose down -v`, and never
reinitializes the database.

### Intentional database actions

Alembic migrations are run only when they are explicitly requested or when the
Git update contains changed files under `backend/migrations/versions/`:

```bash
sudo ./update.sh --migrate
```

The idempotent seed is never run implicitly. Seed changes must be applied
intentionally:

```bash
sudo ./update.sh --seed
```

For a release that intentionally needs both:

```bash
sudo ./update.sh --migrate --seed
```

To force a strictly code-only deployment even when new migration files were
pulled:

```bash
sudo ./update.sh --no-auto-migrate
```

When a database action is intended, the updater creates a PostgreSQL dump first.
A code-only update creates only the regular file backup and does not call
`pg_dump`.

The same code-first runner can be requested from **Staff Panel → System status →
Update server**. The web API never receives the Docker socket or a root shell. It
can only create a constrained request file in `infrastructure/data/control/`.
`rbf-hub-update.path` notices that file and starts the root-owned one-shot
`rbf-hub-update.service`. The Staff Panel action never requests a seed. Changed
Alembic migration files are detected by the host runner.

Only users with the `admin` role may start an update. Staff members may view the
status, update transcript and persisted application/request logs.

## Monitoring

Uptime Kuma is exposed through a TLS-only gateway. Always use:

```text
https://SERVER-IP:8443
```

A request to `http://SERVER-IP:8443` is intentionally rejected by NGINX with
`400 The plain HTTP request was sent to HTTPS port`.

If an older update aborted before its final service-start step, restore the
monitoring services without touching PostgreSQL:

```bash
cd infrastructure
sudo docker compose --env-file .env -f compose.yml --profile monitoring \
  up -d --no-deps uptime-kuma monitoring-gateway
```
