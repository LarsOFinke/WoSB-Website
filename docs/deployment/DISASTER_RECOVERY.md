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

The website enrollment flow provisions each backup target explicitly. The
provisioner response is public; the private read-only SSH key and age identity
stay on the recovery host:

```bash
# Backup server
sudo rbf-recovery-tool targets
sudo rbf-recovery-tool test --target production
sudo rbf-recovery-tool run --target production
sudo rbf-recovery-tool sync --target production
sudo rbf-recovery-tool catalog --target production
```

Test and production profiles use separate local directories and target-specific
pinned SSH fingerprints. A host-key mismatch is a stop condition, not a prompt
to accept a new key. The managed backup server automatically runs `sync` for
each target; run `run` only when a fresh website backup is explicitly required.

## Third-host backup-backup copy

For an additional encrypted copy, a third host may pull the verified artifacts
from the backup server. The backup roots are `/backups/wosb/test` and
`/backups/wosb/production`; they are root-owned and mode `0700` by default.
Use a dedicated administrative SSH identity and a read-only ACL for the exact
backup user if direct `scp -r` access is needed. Do not use the website's
chrooted controller account, whose visible root is `/exports`.

The ACL should grant only read/traverse access to the two backup roots and a
default read ACL for future backup sets. It must not grant access to
`/etc/rbf-recovery-tool`, because that directory contains the private age
identities required for decryption. Keep the third-host copy encrypted at rest
and verify checksums after transfer. A copy of the encrypted artifacts without
the protected identities is intentionally useful as an independent storage
copy, but it is not by itself a complete restore capability.
