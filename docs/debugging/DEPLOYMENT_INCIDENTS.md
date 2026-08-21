# Deployment Incidents and Known Failure Patterns

For failures in local API, frontend, or domain flows, use
[`MODULE_DEBUGGING.md`](MODULE_DEBUGGING.md) first. This document supplements that
workflow with production- and release-related failure patterns.

For initial narrowing from the origin, use `./infrastructure/scripts/diagnostics/debug.sh`
and keep area, category, time range, and line limit as narrow as possible. The locally
redacted file under `.diagnostics/` is the preferred basis for agent analysis; do not
persistently collect raw logs from the target or forward them without review.

## 1. `Permission denied` for scripts

**Symptom:** Delivered runtime scripts such as `install-artifact.sh`, `stop.sh`, or
`install-systemd.sh` cannot be executed after SCP or a root build.

**Cause:** Execute bits or ownership changed during copying or through `sudo ./deploy.sh`.

**Diagnosis and fix:**

```bash
find infrastructure/scripts -type f -name '*.sh' ! -perm -u+x -print
sudo chown -R root:root /opt/rbf/releases/<version>/infrastructure/scripts
sudo find /opt/rbf/releases/<version>/infrastructure/scripts -type f -name '*.sh' -exec chmod 0755 {} +
```

The origin build repairs generated directories for the invoking user; release packages
normalize script permissions. Do not set the entire installation root to `0777`.

## 2. Wrong artifact despite a new version

**Symptom:** Docker shows `rbf-hub-api:1.0.1`, but Spring Boot reports `v1.0.0`.

**Cause:** Multiple JARs remained in the Maven target and the oldest or a stale JAR was packaged.

**Solution:** `build-artifact.sh` deletes old `rbf-api-*.jar` files (except `.original`)
and accepts only `rbf-api-${VERSION}.jar`. Rebuild and transfer with `./update.sh`; do not
reuse an old archive.

## 3. Same version rejected as immutable

**Symptom:** `Immutable release already exists and is active`.

**Cause:** The version number was reused after activation. Activated releases are immutable;
even a later hotfix or documentation correction therefore needs a new patch version.

**Solution:** Classify the change according to [`VERSIONING.md`](../development/VERSIONING.md),
increment `VERSION` and the coupled version sources, and build a new artifact. Never manually
delete the active release, its metadata, `shared/.env`, or `shared/data` to reuse the same version.

## 4. NGINX starts in a restart loop

**Symptom:** `could not open error log file` or
`chown(/var/cache/nginx/client_temp) ... Operation not permitted`.

**Cause:** The container did not run with the permissions expected by the default image for
cache directories while root filesystems were mounted read-only.

**Solution:** Release configuration uses a direct NGINX start, stderr logging, and writable,
correctly owned runtime directories. After a change, always check:

```bash
sudo docker compose --env-file /opt/rbf/shared/.env \
  -f /opt/rbf/current/infrastructure/compose.release.yml ps -a
sudo docker compose --env-file /opt/rbf/shared/.env \
  -f /opt/rbf/current/infrastructure/compose.release.yml logs --tail=200 gateway
```

## 5. systemd fails and logs appear to disappear

**Symptom:** `rbf-hub.service` exits with `status=2/INVALIDARGUMENT`; afterward the
API/Postgres containers are gone.

**Cause:** Activation failure diagnostics were not persisted before Compose cleanup, or a
network remained occupied by an orphaned container.

**Solution:** Current activation first writes
`/opt/rbf/shared/deployments/failed-<version>-<timestamp>.log`. Preserve this file,
`journalctl`, and `docker compose ps -a` first, then clean up deliberately:

```bash
sudo docker ps -aq --filter label=com.docker.compose.project=rbf-hub | xargs -r sudo docker rm -f
sudo docker network ls --filter name=rbf-hub_ --format '{{.ID}}' | xargs -r sudo docker network rm
```

Then redeploy with `./update.sh`. Do not use `docker compose down` as the first diagnostic step.

## 6. PostgreSQL reports “database system is shutting down”

**Symptom:** systemd exits immediately after starting the Postgres container with
`psql ... FATAL: the database system is shutting down`.

**Cause:** A simple port/container check passed before PostgreSQL was actually accepting connections.

**Solution:** The readiness path waits for `pg_isready` and a successful
`psql -c 'select 1'` query. For an isolated test, wait a few seconds and then check the API
readiness endpoint.

## 7. Backup manifest references outside the release tree

**Symptom:** `Artifact is outside the infrastructure tree` for a file under
`/opt/rbf/shared/data/backups`.

**Cause:** The manifest generator incorrectly expected shared backups to live under
`/opt/rbf/<release>/infrastructure`.

**Current operational decision:** Origin deployments temporarily use `--skip-backup`; the backup
runner remains available for manual testing until path modeling is corrected separately and a
restore is revalidated.

## 8. 401 on registration or anonymous endpoints

**Symptom:** `POST /api/auth/register` or cookie/privacy endpoints return 401; NGINX shows the
request, but the API log contains no matching security entry.

**Diagnosis:**

```bash
sudo docker compose --env-file /opt/rbf/shared/.env \
  -f /opt/rbf/current/infrastructure/compose.release.yml logs --since=10m api gateway
```

Verify that the running JAR matches the release version. Security configuration explicitly allows
the anonymous methods and ignores CSRF only for those routes; 401/403 logs contain only method,
path, and boolean context indicators.

## 9. 401 despite a session cookie on protected routes

**Symptom:** Logged-in requests return 401; the API log also contains a
`LazyInitializationException` for `SiteRoleEntity`, followed by a 401 for `/error`.

**Cause:** The session filter creates Spring authentication after the repository call has ended.
If the site role is returned only as a lazy proxy, the filter can no longer load its permissions.
The protected error path then hides the original exception.

**Solution:** The authentication query must load user and site role with an explicit fetch join.
`/error` remains public so follow-up failures do not appear as a misleading 401. Keep the browser
session after deployment; logging in again is necessary only when the session has expired.

## 10. Cookie settings are not shown automatically

If the consent endpoint reports no stored decision, the dialog opens automatically. If the
endpoint fails, the dialog remains visible with settings open so optional processing stays
disabled and the user can retry or make an explicit choice. Settings also remain available
through the footer and privacy center. The consent GET and POST responses are deliberately
`Cache-Control: no-store, private`, and the browser request also bypasses its cache; a cached
`has_decision:true` response must not suppress a fresh user's banner. In browser diagnostics,
inspect `[privacy] cookie_consent_initialize_*` events and correlate a failed request's status
and `X-Request-Id` with `privacy_cookie_consent_state` or `api_error` server logs. These logs
record only cookie presence/validity and decision state, never consent keys or payloads. They are
development-only and must not appear in production builds. The rendered surface intentionally
uses application-specific `rbf-choice-*` selectors: generic `cookie-consent`/`consent` selectors are
commonly hidden by browser privacy extensions, which can leave the Vue state visible while
removing the dialog from the screen. Do not share production cookies in tickets.

## 11. Versions do not match

`VERSION`, `spring-api/pom.xml`, frontend `package.json`, and the lockfile must carry the same
version. `infrastructure/scripts/quality/check_repository.py --strict-tree` and the origin build
intentionally fail on mismatches.

## 12. First start fails during a monitoring image pull

**Symptom:** API and PostgreSQL are ready, but release startup ends during download of
`louislam/uptime-kuma` with a failed health check.

**Cause:** The optional monitoring stack blocked the critical systemd startup path and could exceed
the activation window.

**Current state:** Uptime Kuma and its separate gateway have been removed from production Compose,
setup, backup/restore, and the frontend. A new deployment starts only PostgreSQL, Spring Boot, and
the main gateway. Orphaned monitoring containers are removed by `--remove-orphans` on the next start.

## 12. `current` is not a symlink

**Symptom:** `Current installation entry is not a symbolic link.`

**Cause:** An earlier aborted setup run left a real `/opt/rbf/current` directory behind.

**Solution:** Origin deployment now calls cleanup with `--replace-active --yes`. Such an entry is
removed only when it contains `infrastructure/compose.release.yml`; `/opt/rbf/shared` remains
untouched. Unknown or unsafe entries continue to be rejected fail-closed.

## 13. HTTP 500 for calendar or staff date filters

**Symptom:** Calendar, staff overview, or date filters for registrations, audit logs, and the
security dashboard return HTTP 500. The API log shows `MethodArgumentTypeMismatchException` for
`LocalDate` or `LocalDateTime`.

**Cause:** Browsers send contract-compliant ISO values (`YYYY-MM-DD` or UTC timestamps with `Z`),
while generated Spring controllers previously used the locale-dependent default converter. The
global error handler also classified the expected binding failure as an unexpected server error.

**Solution:** The route generator annotates `date` and `date-time` query parameters with explicit
ISO format. Invalid parameters return a bounded HTTP 400 response. Do not fix generated controllers
directly; always correct `openapi/openapi.json` and controller bindings together and verify with
`audit_controller_contract.py`.

## 14. HTTP 500 for master-data categories

**Symptom:** `/api/admin/master-data/categories` returns HTTP 500; the API log contains
`UnrecognizedPropertyException` for `seed_checksum`.

**Cause:** The database query includes internal seed metadata that intentionally is not part of the
public read contract. Strict contract conversion correctly rejects unknown properties.

**Solution:** Remove internal seed checksums, relational IDs, and helper columns at the master-data
mapping boundary before converting categories, options, or ships into API contracts. Do not extend
the contract with internal database fields and do not globally configure Jackson to ignore unknown fields.

## 15. HTTP 500 in the security dashboard

**Symptom:** `/api/admin/logs/security-dashboard` returns HTTP 500; the API log contains
`ClassCastException: java.sql.Date cannot be cast to java.time.LocalDate`.

**Cause:** PostgreSQL `DATE` values arrive through JDBC as `java.sql.Date`, while the service cast
them directly to `LocalDate`.

**Solution:** Normalize date types at the shared persistence boundary through `RowValues.date`.
The regression test deliberately uses `java.sql.Date` so a pure mock with an already-converted
`LocalDate` cannot hide the failure.

## 16. NGINX cannot inspect the maintenance marker

**Symptom:** Gateway logs contain `stat() ... maintenance-mode.json failed (13: Permission denied)`
for requests.

**Cause:** The unprivileged gateway process with UID 101 could not traverse the control directory
restricted to group 10001.

**Solution:** In both Compose files, the gateway receives only the additional numeric runtime group
10001. Status remains mounted read-only; directory permissions are not opened globally.
