# Master data seeding and administration

This document describes the master-data ownership model introduced for the Build Designer catalog and ship catalog.

## Scope

The managed master data currently includes:

- Build item categories;
- equipment options such as sails, upgrades, lanterns, ammunition, consumables, hold items, weapons and Specialists;
- option stat effects and allowed weapon slot types;
- ships and their performance values;
- ship weapon mounts, maximum weapon classes and mortar calibers;
- image references for ships and equipment options.

The normalized weapon-class and weapon-slot taxonomy remains seed-managed infrastructure. It is available to the admin editor as selectable reference data, but is not editable there because changing taxonomy codes would require a coordinated data migration.

## Findings from the previous implementation

The previous seed manager used the Python seed lists as an unconditional source of truth. On every seed run it copied their values back into existing ship and option rows. This had four operational consequences:

1. A manual database correction could be overwritten by the next seed.
2. There was no durable distinction between a shipped default and a fleet-specific value.
3. Display names doubled as record identity, making later renames fragile.
4. The data could only be maintained by editing Python and running a seed; there was no admin workflow.

The Build Designer itself already had a sound normalized base for options, effects, slot eligibility and ship weapon mounts. The redesign therefore keeps those tables and adds explicit data ownership instead of creating a second catalog.

## Ownership model

`build_item_categories`, `build_item_options` and `ships` now contain:

- `seed_key`: stable identity of a shipped default;
- `seed_revision`: revision that last applied the default;
- `seed_checksum`: checksum of the canonical seed payload;
- `is_seed_overridden`: whether an administrator deliberately owns the current values.

The resulting states are:

| State | Meaning | Behavior during a seed |
| --- | --- | --- |
| Seed default | Has `seed_key`, override is false | Updated only when revision or checksum changed |
| Admin override | Has `seed_key`, override is true | Preserved exactly |
| Custom | Has no `seed_key`, revision is `custom` | Never adopted or overwritten |
| Retired default | Has `seed_key`, inactive, no current checksum | Kept for historical references and reactivated if reintroduced |

Deleting master data from the admin UI is intentionally a soft deactivation. Existing Builds continue to resolve their foreign-key references, while inactive records disappear from new Build Designer selections.

## Seed maintenance workflow

Seed source files remain split by domain under `backend/src/app/seeds/`. The central synchronization behavior lives in `catalog_sync.py` and `manager.py`.

When changing a shipped default:

1. Edit the relevant domain file, for example `upgrades.py` or `ships.py`.
2. Keep its stable identity. Existing rows default to their original name as identity. When renaming a seed, add `seed_id` with the previous stable value rather than allowing the name change to create a second record.
3. Bump `MASTER_DATA_SEED_REVISION` for a reviewed catalog release.
4. Run the backend tests and the seed against a copy of production data before deployment.
5. Deploy with Alembic migration and an explicit seed run.

Example rename:

```python
{
    "seed_id": "Old Display Name",
    "name": "New Display Name",
    # remaining fields
}
```

The checksum is calculated from semantic data. Database-specific foreign-key IDs are not part of the option checksum. Unchanged defaults are skipped, reducing writes and avoiding meaningless timestamp churn.

A new seed that collides with an admin-created custom record fails loudly instead of silently converting the custom record into a seed-owned row. Resolve the collision by renaming the custom record or assigning a different `seed_id` in code.

## Admin UI

Administrators can open `/admin/master-data` from the staff dashboard. Backend authorization is enforced by `require_admin`; moderators and other staff roles cannot use these endpoints.

The page provides three workspaces:

- categories: label, ordering and active state;
- options: category, name, source, notes, option type, image, weapon metadata, allowed slots, stat effects, ordering and active state;
- ships: all Build Designer ship values, image, sail/upgrade/lantern capabilities and normalized weapon mounts.

For images, an administrator can either enter an external or internal image reference or upload an image through the existing file service. Uploaded records store the portable `/uploads/...` path. The frontend resolves that path against the API origin in development and uses the same-origin path in production.

Editing or deactivating a shipped default creates an admin override. The `Restore seed default` action clears that override and reapplies the current default, including nested effects, slot links and weapon mounts.

## API

All routes are below `/api/admin/master-data`:

- `GET /overview`
- `GET /taxonomy`
- `GET|POST /categories`
- `PUT|DELETE /categories/{id}`
- `POST /categories/{id}/restore-seed`
- `GET|POST /options`
- `PUT|DELETE /options/{id}`
- `POST /options/{id}/restore-seed`
- `GET|POST /ships`
- `PUT|DELETE /ships/{id}`
- `POST /ships/{id}/restore-seed`

## Migration and deployment

Alembic revision `a1b2c3d4e5f6` adds the ownership metadata, unique seed-key indexes and image fields. Production remains migration-owned and should be updated through the normal operations workflow, for example:

```bash
sudo ./update.sh --migrate --seed
```

Do not reset the database. The first seed after migration adopts matching legacy shipped rows and assigns their seed metadata. Existing Builds and their option references are retained.

For local SQLite databases in create mode, `init_db.py` also adds the compatibility columns and unique indexes to older prototype databases.

## Validation and tests

The implementation is covered by regression tests for:

- admin-only API access;
- preservation of option and ship overrides across repeated seed runs;
- restoration of current seed defaults;
- preservation of admin-created custom records;
- existing catalog completeness and weapon eligibility rules;
- full backend regression suite;
- locale completeness;
- Build Designer inventory behavior;
- production frontend build;
- a fresh SQLite Alembic upgrade to the new head revision.

## Deliberate boundaries

The image editor references the existing file service but does not provide a media-library browser or automatic deletion of replaced uploads. This avoids deleting a file that may still be referenced elsewhere. A future media-library feature should add reference counting or an explicit asset-to-master-data relation before introducing automatic cleanup.

Weapon class and slot-type definitions are read-only in this admin page. Their codes participate in compatibility logic and should continue to change through migrations and reviewed seed changes rather than ad hoc edits.
