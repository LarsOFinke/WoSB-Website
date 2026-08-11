# Backup architecture

A coordinated backup set is committed only when all of these artifacts belong to the same application boundary:

1. PostgreSQL custom-format dump and checksum.
2. Persistent upload/files archive and checksum.
3. Restore-preflight report from an isolated database and Spring instance.
4. Set manifest binding filenames, sizes, hashes, application version and Flyway version.
5. For disaster recovery, the exact compiled release artifact plus encrypted configuration and host-control secrets.

The API only creates a signed intent file. A root-owned runner validates ownership, link count, permissions and size before executing a fixed operation. No user-controlled command or path is evaluated.

Database restore always imports into a staging database first. The active Spring image applies and validates Flyway, reaches readiness, and only then may the staging database be atomically activated. A failed activation restores the previous database.

Recovery bundles are encrypted with `age`, contain a complete SHA-256 inventory, reject links and special entries during extraction, and can be verified without modifying production.

The strategy planner remains inside this existing aggregate boundary. Its documents,
publication state, and catalog references are included by the unrestricted PostgreSQL
custom dump; its background assets are included by the complete `uploads/` archive.
The recovery client therefore transfers and verifies both artifacts together rather
than maintaining a strategy-specific inventory that could drift from the schema.

## Partial logical migration is not disaster recovery

A build-only recovery from a legacy Python dump is handled as a reviewed logical
data migration, not by restoring the old database over the current installation.
The target remains on the current Flyway schema and current master data; only the
required aggregate is reconstructed using semantic references and explicit owner
mapping. The exact migration artifact must pass a transactional dry-run and a
committed verification on the test server before the same artifact can be used
on production. See
[`../debugging/LEGACY_BUILD_DATA_MIGRATION.md`](../debugging/LEGACY_BUILD_DATA_MIGRATION.md).
