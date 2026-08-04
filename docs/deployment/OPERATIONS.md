# Production operations

## Services

Core services are `postgres`, `api` and `gateway`. The former Uptime Kuma
monitoring profile has been removed from the production stack.

```bash
sudo /srv/rbf/current/infrastructure/scripts/services/status.sh
sudo /srv/rbf/current/infrastructure/scripts/checks/doctor.sh
sudo /srv/rbf/current/infrastructure/scripts/checks/smoke-test.sh
```

Spring readiness is available internally at `/actuator/health/readiness`; the public gateway exposes the application health contract.

## Updates from the origin host

Updates, restarts and rollbacks are deliberately not triggered from the web
application. Start them on the trusted origin server through the repository
dispatcher, for example:

```bash
sudo ./update.sh --artifact /srv/releases/rbf-deployment-1.0.1.tar.gz
```

The dispatcher cleans failed releases and replaces an active release with the
same version before installing the verified artifact. It also removes stale
Spring Boot JARs during the origin build, so the image tag and the application
version cannot silently diverge. Do not run `infrastructure/scripts/services/update.sh`
or the former Admin-Panel update path to activate an artifact on the website
server; that runner now fails closed. `--restart` and `--rollback` remain valid
local recovery operations.

Für lokale Wartungsaktionen auf dem Zielserver bleiben die versionierten
Runner unter `/srv/rbf/current/infrastructure/scripts/services/` verfügbar.

The target host still exposes read-only status for operations monitoring.

## Logs

```bash
sudo /srv/rbf/current/infrastructure/scripts/services/logs.sh
sudo journalctl -u rbf-hub.service -u rbf-hub-backup.service
```

Never copy secrets, cookies, authorization headers or raw personal payloads into tickets.

## Database changes

Flyway runs during API startup before readiness. Failed or checksum-inconsistent migrations keep the API unready. Published migrations are immutable; destructive cleanup is delayed until all supported releases no longer depend on the old shape.

## Backup routine

Every normal origin deployment creates the coordinated backup set before the
release switch. The backup routine can also be run manually:

```bash
sudo /srv/rbf/current/infrastructure/scripts/backup/run-consistent-backup.sh --reason scheduled
```

A backup is healthy only if its manifest references a passed isolated restore
preflight. If this preflight fails, the update stops before `current` changes.
Periodically perform a full recovery exercise on a separate host.
