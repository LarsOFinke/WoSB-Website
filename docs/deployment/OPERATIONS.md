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

## Updates from the origin host or staff panel

Normal releases are still built and transferred from the trusted origin server,
for example:

```bash
sudo ./update.sh --artifact /srv/releases/rbf-deployment-1.0.0.tar.gz
```

The dispatcher cleans failed releases and replaces an active release with the
same version before installing the verified artifact. The staff panel can also
queue `update`, `restart`, or `rollback` through the root-owned systemd watcher.
An update is accepted only when a checksummed artifact is already staged in
`/srv/rbf/shared/releases/inbox`; the host runner then uses the same coordinated
backup, migration, activation and rollback path as a normal release.

Für lokale Wartungsaktionen auf dem Zielserver bleiben die versionierten
Runner unter `/srv/rbf/current/infrastructure/scripts/services/` verfügbar.

The target host exposes operation status and a guarded staff-panel request path.

## Logs

Vom vertrauenswürdigen Ursprungssystem ist der bevorzugte Einstieg:

```bash
./infrastructure/scripts/diagnostics/debug.sh

# Nicht-interaktiv und bereits stark eingegrenzt:
./infrastructure/scripts/diagnostics/debug.sh --area calendar --category http-500 --since 30m --tail 400
./infrastructure/scripts/diagnostics/debug.sh --area staff --category errors --since 1h --match MethodArgumentTypeMismatchException
```

Der Wrapper verwendet standardmäßig die von `deploy.sh --configure` gepflegte
`.env.origin.test`. Production-Diagnosen erfordern `--production` und verwenden
`.env.origin.production`; beide Profile enthalten ihren eigenen SSH-Key-/Host-
Kontext und `sudo -n`. Bereiche sind `overview`,
`staff`, `calendar`, `api`, `security`, `gateway`, `database`, `deployment` und
`all`; Kategorien sind `errors`, `warnings`, `http-500`, `auth`, `migration`
und `all`. Zeitraum und Zeilenlimit sind validiert und begrenzt. `--match`
ergänzt einen literalen Suchtext.

Die Rohdaten werden nur gestreamt. Auf dem Zielsystem entsteht kein
Diagnosearchiv. Am Ursprung entfernt der Collector ANSI-Steuerzeichen,
IP-/E-Mail-Adressen, Querywerte und typische Credential-Felder und speichert das
Ergebnis standardmäßig mit Modus `0600` unter `.diagnostics/*.log`. Der Pfad wird
am Ende ausgegeben und kann einem Agenten für eine gezielte Analyse genannt
werden. Vor externer Weitergabe trotzdem manuell prüfen; niemals Rohlogs,
Secrets, Cookies, Authorization-Header oder personenbezogene Payloads in Tickets
kopieren.

Direkt auf dem Zielserver bleiben für einen Operator verfügbar:

```bash
sudo /srv/rbf/current/infrastructure/scripts/services/logs.sh
sudo journalctl -u rbf-hub.service -u rbf-hub-backup.service
```

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

## Test/Production TLS and target isolation

Origin deployment targets and website runtime identities are separate. `deploy.sh`/`update.sh` default to `test`; Production always requires `--production`. The selected target is written to the private website `.env` as `DEPLOYMENT_ENVIRONMENT` and must never be inferred from a certificate or hostname.

Production is fail-closed: `TLS_MODE=letsencrypt`, a public `APP_HOSTNAME`, a configured `LETSENCRYPT_EMAIL`, and `LETSENCRYPT_STAGING=false` are mandatory. Test may use self-signed TLS or Let's Encrypt staging. Staging certificates are deliberately never promoted to Production. Each target obtains and renews its own certificate in its own shared data tree.

Before `fullchain.pem`/`privkey.pem` are atomically replaced, the TLS helper verifies the certificate hostname, certificate/private-key match and at least seven days of remaining validity. The certificate renewal timer keeps using Certbot's deploy hook, so nginx is reloaded only after a successful validated renewal. Release artifacts contain neither target `.env` files nor certificates. Coordinated file backups include the target-local certificate and Let's Encrypt state for disaster recovery.

The release compose file does not publish PostgreSQL to the host. Database inspection uses bounded `docker compose exec -T`/diagnostic helpers; interactive production containers are not a normal debugging interface.
