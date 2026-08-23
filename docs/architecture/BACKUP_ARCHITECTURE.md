# Backup architecture

A coordinated backup set commits only when it binds the PostgreSQL dump, files
archive, successful isolated Spring/Flyway restore report, set manifest, and
age-encrypted recovery bundle containing the release and protected recovery
configuration.

The web API writes only signed operation intents. A root-owned runner validates
them and executes fixed operations. Restore always stages the database, runs
Flyway and readiness checks, and only then may activate it.

## Controller-pull trust boundary

The backup server is the control instance. Its Recovery Tool connects outbound
to the stable website SSH endpoint, requests backups, verifies them locally,
controls retention, and acknowledges durable storage. The website does not know
how to reach the backup server.

The website exposes one chrooted SFTP account per environment. It may create
request and acknowledgement files and read root-published exports/status. It has
no shell, forwarding, password authentication, or export write access. Private
controller SSH and age keys remain on the backup server.

This limits a compromised website: it cannot connect to the backup server or
read/delete durable `/backups` data. It can withhold or produce future data,
which the controller accepts only after complete recovery proof validation. A
compromised controller can request and read deliberately exported encrypted
sets, but receives no general website shell.

Pre-update deployment always creates and verifies a complete local backup set.
It attempts to obtain a controller acknowledgement for the exact manifest
digest, but a temporarily unavailable controller does not block activation by
default; operators can set `BACKUP_REQUIRE_PULL_ACK_BEFORE_UPDATE=true` for a
strict fail-closed policy. Manual controller operation is supported with an
explicit target selection.

Test and production use separate accounts, chroots, keys, age identities,
profiles, state files, and `/backups/wosb/<environment>` roots. Automatic
controller timers are intentionally disabled; operators select the target for
each manual run. A
cross-environment request or response fails validation.

The origin deployment profiles are also separate. Each owns the website SSH
host and port reachable by the backup server, and every deployment reconciles
only the selected profile into that target's private environment. Enrollment
does not infer SSH routing from the public application hostname.

The strategy planner stays inside the aggregate: relational state is in the
PostgreSQL dump and chart backgrounds are in `uploads/`. Partial build-only
imports are logical migrations, not disaster recovery; see
[Legacy build data migration](../debugging/LEGACY_BUILD_DATA_MIGRATION.md).
