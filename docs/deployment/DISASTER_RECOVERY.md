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
