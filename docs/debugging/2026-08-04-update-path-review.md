# Update Path and Database Preservation

## Finding

The previous origin dispatcher passed `--skip-backup --no-backup` to the target host
and removed the active release before installation with `--replace-active`. Although this
preserved `/opt/rbf/shared`, it bypassed the intended coordinated pre-deployment protection.

## Correction

- `deploy-from-origin.sh` cleans only failed/inactive releases.
- The active release remains in place until backup and readiness checks succeed.
- Normal updates pass neither `--skip-backup` nor `--no-backup`.
- Before switching releases, `install-artifact.sh` invokes
  `run-consistent-backup.sh` from the previous release.
- If backup, migration, readiness, or smoke tests fail, the old release remains active or
  is restored together with the backup artifacts.

## Data and migration path

1. PostgreSQL is bind-mounted under `/srv/rbf/shared/data/postgres`.
2. The release links `infrastructure/data` to `/srv/rbf/shared/data`.
3. The backup runner quiesces the API, creates the dump, file backup, recovery/restore
   preflight, and backup-set manifest, then starts the API again.
4. Only then is the new release built and atomically activated as `current`.
5. On API startup, Flyway applies new immutable migrations; Hibernate remains set to `validate`.
6. The update path does not use `docker compose down -v`.

## First installation and root migration

Automatic target installation initially stopped during a non-interactive first run at the
`First installation requires explicit --no-backup` safeguard. `setup_website.sh` now detects
a genuinely empty target root without active or leftover releases and grants first-installation
approval internally. If releases or an active `current` exist, the coordinated backup path
remains unchanged.

An existing installation under `/opt/rbf` is moved in a controlled manner to `/srv/rbf`
before environment preparation. The migration helper is transferred both inside the release
artifact and separately from the origin server so older already-built artifacts can also be
migrated fail-closed.

## Regression gates

`infrastructure/scripts/quality/tests/update-management.sh` statically verifies that the origin
dispatcher contains no backup-skip or active-replacement flags and that installer and Docker
lifecycle still invoke the backup/Flyway steps.

## SSH dispatcher without password fallback

The interactive password prompt occurred because `.env.origin` used the private application
account and the dispatcher did not pass a fixed identity file. The dispatcher now supports
`RBF_DEPLOY_IDENTITY_FILE` or `--identity-file` and sets `BatchMode=yes` and
`IdentitiesOnly=yes` for all SSH/SCP calls. This exposes an incorrectly configured key path
immediately instead of asking for a password during unattended execution. After the one-time
bootstrap of the dedicated account, test access in a second session before activating it in
`.env.origin`.

For freshly installed target systems, `deploy.sh` now performs this transition in the same run.
If the key-only preflight fails, an existing initial user can be supplied interactively or with
`--bootstrap-user`. Only the SSH provisioner and public key are staged through this connection.
After setup and SSH reload, the new `rbfadmin` preflight including `sudo -n` must succeed before
build or release installation begins. The initial user is not persisted in origin configuration.

Bootstrap does not require password login. Without an explicit bootstrap identity, OpenSSH
selects from SSH configuration, agent, and standard keys and uses a password only when the server
allows it. With `--bootstrap-identity-file`, the specified VPS key is used exclusively and in
batch mode. For initial root access the provisioner runs directly; for other accounts it runs
through `sudo`.
