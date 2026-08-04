# Production operations

## Services

Core services are `postgres`, `api` and `gateway`. Optional monitoring uses the `monitoring` Compose profile.

```bash
sudo /opt/rbf/current/infrastructure/scripts/services/status.sh
sudo /opt/rbf/current/infrastructure/scripts/checks/doctor.sh
sudo /opt/rbf/current/infrastructure/scripts/checks/smoke-test.sh
```

Spring readiness is available internally at `/actuator/health/readiness`; the public gateway exposes the application health contract.

## Admin operations

Administrators may request only:

- `update`: install the newest staged, checksummed release artifact;
- `restart`: restart API and gateway without changing PostgreSQL;
- `rollback`: restore the previous release and its coordinated database backup.

The API writes an owner-only request file. The root runner claims it securely and accepts no arbitrary command arguments from HTTP.

## Logs

```bash
sudo /opt/rbf/current/infrastructure/scripts/services/logs.sh
sudo journalctl -u rbf-update-runner -u rbf-backup-runner
```

Never copy secrets, cookies, authorization headers or raw personal payloads into tickets.

## Database changes

Flyway runs during API startup before readiness. Failed or checksum-inconsistent migrations keep the API unready. Published migrations are immutable; destructive cleanup is delayed until all supported releases no longer depend on the old shape.

## Backup routine

```bash
sudo /opt/rbf/current/infrastructure/scripts/backup/run-consistent-backup.sh --reason scheduled
```

A backup is healthy only if its manifest references a passed isolated restore preflight. Periodically perform a full recovery exercise on a separate host.
