# Disaster recovery

## Recovery contract

A usable encrypted recovery bundle contains:

- PostgreSQL custom dump and checksum;
- persistent file archive and checksum;
- the exact compiled deployment artifact and checksum;
- environment configuration and required host-control secrets;
- version, Flyway and inventory metadata.

## Verify without activation

```bash
sudo infrastructure/scripts/backup/restore-recovery.sh \
  --bundle rbf-recovery-<timestamp>.tar.gz.age \
  --identity /secure/age-identity.txt \
  --verify-only
```

Verification decrypts into a private temporary directory, rejects unsafe archive entries, validates all hashes, checks the release manifest and runs `pg_restore --list` without changing production.

## Full restore

On a replacement host:

1. install Docker/Compose, `age`, Python 3 and PostgreSQL client utilities;
2. restore the bundle with explicit `--yes` confirmation;
3. install the exact release artifact into `/srv/rbf`;
4. restore persistent files;
5. import the database into staging;
6. start the matching Spring image against staging and require Flyway validation and readiness;
7. atomically activate the database;
8. run HTTPS smoke tests and record the recovery report.

```bash
sudo infrastructure/scripts/backup/restore-recovery.sh \
  --bundle rbf-recovery-<timestamp>.tar.gz.age \
  --identity /secure/age-identity.txt \
  --yes \
  --replace-existing
```

Never activate a database that did not pass the isolated application preflight. Keep the previous database until the post-activation smoke test has succeeded.

## Routine pulls with the recovery client

The standalone client is restored under `tools/recovery-tool/` and follows the
same current contract: backup-set schema 1, Spring/Flyway preflight schema 2,
and recovery-bundle schema 2 with the exact release artifact. It does not use
the old Python-backend repository or ask the website to perform routine pulls.

Configure each backup target explicitly. The provisioner response is public;
the private read-only SSH key and age identity stay on the recovery host:

```text
rbf-recovery-tool setup --target test --local-backup-host
rbf-recovery-tool setup --target production --local-backup-host
rbf-recovery-tool targets
rbf-recovery-tool pull --target production
```

Setup selects a single valid response from `~/Downloads` by JSON content. If
multiple responses exist, pass `--response /path/to/file.json` to select the
intended target explicitly.

Test and production profiles use separate local directories and target-specific
Linux timers. The setup command performs a live comparison with the response's
pinned SSH fingerprint. If an offline import is unavoidable, use `--offline`
only temporarily and run `rbf-recovery-tool test --target <target>` before a
pull. A host-key mismatch is a stop condition, not a prompt to accept a new key.
