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
