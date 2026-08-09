# Legacy build data migration (Python -> Spring Boot)

This runbook covers a **logical, build-only data migration** from a legacy
PostgreSQL dump into an already installed and Flyway-migrated Spring Boot
installation.

It is deliberately different from disaster recovery. Do not restore the old
whole-database dump over a current installation merely to recover builds.
Legacy dumps can contain users, password hashes, sessions, audit data, obsolete
seed identifiers, old schema DDL and historical sequences that do not belong in
the current runtime.

## When to use this procedure

Use this path when all of the following are true:

- only build data needs to be recovered or transferred;
- the target Spring Boot installation is already healthy and migrated;
- the logical build schema is still compatible;
- legacy technical foreign-key IDs or seed keys may differ from the current
  Java seed catalog;
- the import has first been tested against the test server.

For a complete installation recovery use
[`../deployment/DISASTER_RECOVERY.md`](../deployment/DISASTER_RECOVERY.md)
instead.

## Data boundary

The reviewed build-only migration contains only the logical build aggregate:

- `builds`;
- `build_slots`;
- `build_classifications`.

It intentionally does **not** import:

- users or password hashes;
- auth sessions;
- audit data;
- votes, guides, groups or files;
- master/seed rows;
- Flyway history;
- DDL, constraints or sequences.

Owners are mapped to users that already exist on the target installation.
Historical numeric user, ship, option or feature IDs must never be copied
across environments.

## Reference resolution

A portable migration resolves references by functional identity rather than by
legacy numeric IDs.

For the reviewed Python -> Java build migration the resolver uses:

- ships: legacy seed key, current Java seed key, then unique ship name;
- build options: legacy seed key, current Java seed key, then category + unique
  option name;
- build roles: role slug;
- research feature: feature code;
- owners: explicit source-username -> target-username mapping.

All available identities must resolve to exactly one target row. A missing or
ambiguous match is an import failure, not a reason to guess an ID or edit target
master data during the restore.

This is important because adopted databases can preserve manually overridden
seed state while the functional catalog entry remains the same. A migration may
therefore tolerate technical seed-key drift but must remain fail-closed on
semantic ambiguity.

## Required preflight checks

Before inserting data, a logical migration must verify at least:

1. required target tables/columns exist;
2. source-stage row and foreign-key closure is complete;
3. every owner mapping resolves to exactly one existing target user;
4. ships/options/roles/features resolve unambiguously;
5. slot type and option category remain compatible;
6. classifications and list-size limits remain valid;
7. no duplicate slot positions or duplicate logical items exist;
8. current weapon mount/capacity/caliber rules still accept the build;
9. current upgrade-slot and lantern rules still accept the build;
10. current crew minimum/effective-capacity rules still accept the build;
11. an existing logical target build is either identical or the import aborts;
12. post-import counts and logical relations match the staged backup.

Do not weaken one of these checks merely to make an old dump importable. Resolve
and document the actual Python -> Java semantic difference instead.

## Run the guided restore from the origin system

Use the origin-side restore script with the same separate SSH profiles as deploy,
update and diagnostics. Test is the default target:

```bash
infrastructure/scripts/migration/restore-builds-from-origin.sh
```

The script discovers a portable `rbf-builds-partial-*.sql` artifact in
`backups/`, asks how each historical owner maps to an existing target username,
uploads the exact artifact, verifies its SHA-256 checksum and runs the complete
import as a transaction that is rolled back. If more than one matching artifact
exists, select one explicitly with `--backup`.

Mappings can also be supplied up front:

```bash
infrastructure/scripts/migration/restore-builds-from-origin.sh \
  --owner puszpang=admin \
  --owner nostrapi=admin
```

Use `--dry-run-only` when only validation is wanted. This mode also works without
an interactive terminal and can never commit data.

The SSH deployment user never receives write access to `/srv/rbf`. The remote
helper installs the checksummed artifact as root with mode `0600` below
`/srv/rbf/shared/imports`, acquires the update lock and uses the target-local
Docker/environment helpers. Database credentials are never copied to the origin.

A successful dry run must explicitly report:

```text
DRY RUN successful; rolling back all changes.
```

Any `ERROR`, missing/ambiguous reference, compatibility failure or conflicting
existing build stops the procedure. The script does not offer the commit prompt
until the dry run is completely green.

## Commit the test-server import

After the dry run, type the displayed target-specific confirmation. The remote
helper creates an atomic PostgreSQL custom-format safety dump, verifies its
checksum and `pg_restore` inventory, and then executes the same SQL artifact with
`dry_run=0`. A failed safety dump prevents the import. The update and backup locks
remain held across dump and import so neither a deployment nor a scheduled backup
can race the migration. Because this operation changes only transactional database
rows, it deliberately does not run the much slower full recovery preflight, file
backup, staging-database restore, or application restart.

The current Spring API reads build state from PostgreSQL on request; a server
restart is normally not required after this build-only import. Verify several
representative builds through the API/UI immediately after commit, including
opening and saving builds with different ships, weapon layouts and upgrades.
If build caching is introduced in the future, this no-restart assumption must
be revisited explicitly.

## Promotion to production

Only promote a migration file after the **same file** has passed the complete
Dry-Run -> Commit -> UI/API verification cycle on the test server.

Use the identical SQL file on production. Environment-specific differences
must be passed only through explicit owner mappings. Do not regenerate a second
production-specific data dump after test verification, as that removes the
exact-artifact guarantee:

```bash
infrastructure/scripts/migration/restore-builds-from-origin.sh --production
```

Production selection and commit are separate explicit decisions: the command
requires `--production`, performs another rollback-only dry run, and then asks
for the exact production confirmation phrase.

The guided workflow enforces:

1. current coordinated backup before import;
2. production-specific owner mapping to existing users;
3. another dry-run on the production database;
4. committed import only after the production dry-run is green;
5. immediate API/UI verification after commit.

## Debugging a failed preflight

A failed preflight is useful evidence. Work from the first error only.

Typical Python -> Java drift classes are:

- case or prefix changes in technical seed keys;
- manually preserved/overridden seed keys in an adopted database;
- renamed catalog entries;
- removed or newly constrained slot types/options;
- changed weapon mount, capacity or upgrade rules;
- missing target owners.

For a technical seed-key drift, first prove that the legacy and Java rows are
still the same functional entity. Then extend semantic resolution using stable
business attributes. Never hardcode current numeric database IDs into the
portable migration.

If the failure instead shows a genuinely missing or ambiguous functional
entity, stop and review master-data migration separately.

## Durable rule

A partial data restore is a **migration artifact**, not an application release
artifact and not a full backup. Keep the source dump and reviewed logical
migration immutable once production has used them, record their hashes outside
the repository if retained operationally, and keep customer/production data out
of Git.
