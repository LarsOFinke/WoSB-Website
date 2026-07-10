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

Use `update.sh` for regular releases:

```bash
sudo ./update.sh
```

The update runner:

1. refuses to overwrite tracked local source changes;
2. performs a fast-forward-only Git update;
3. creates a PostgreSQL/upload backup;
4. rebuilds API and gateway images;
5. runs Alembic migrations and the idempotent seed;
6. recreates the application services;
7. runs the application and monitoring smoke tests.

The same runner can be requested from **Staff Panel → System status → Update
server**. The web API never receives the Docker socket or a root shell. It can
only create a constrained request file in `infrastructure/data/control/`.
`rbf-hub-update.path` notices that file and starts the root-owned one-shot
`rbf-hub-update.service`. Status and the last update log lines are written back
to the same directory for read-only display in the Staff Panel.

Only users with the `admin` role may start an update. Staff members may view the
status, update transcript and persisted application/request logs.

## Monitoring

Uptime Kuma is exposed through a TLS-only gateway. Always use:

```text
https://SERVER-IP:8443
```

A request to `http://SERVER-IP:8443` is intentionally rejected by NGINX with
`400 The plain HTTP request was sent to HTTPS port`.
