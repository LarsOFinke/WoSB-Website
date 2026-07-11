# Spring cleanup: profile directory data and 3NF

## Source of truth

Optional member directory data belongs to `user_profiles`:

- availability
- timezone
- Discord handle
- preferred focus
- free profile note

Preferred ships and fleet roles are normalized relations:

- `user_profile_ship_preferences` references `ships.id`
- `user_profile_role_preferences` references `fleet_roles.id`

`fleet_memberships` now contains only facts about the membership itself: fleet, user, role, status, application note, assignment, internal note and timestamps. Fleet management reads profile details through the member relation and cannot overwrite user-owned profile fields.

## Migration

Migration `b2c3d4e5f6a7_profile_directory_3nf.py`:

1. adds profile directory columns;
2. creates normalized preference tables;
3. copies existing membership directory values;
4. maps existing textual ship preferences to the ship catalog where names match;
5. removes the obsolete membership columns and join table.

The migration was validated from an empty database through Alembic head.

## API boundaries

- `PUT /api/profile` is the only write path for personal directory data.
- `GET /api/profile/preferences/options` exposes selectable ships and fleet roles.
- fleet application accepts only the fleet id and an application note.
- fleet membership administration updates only membership-owned fields.

## KISS and SOLID decisions

- A single profile service validates and persists profile preferences.
- Schemas reject invalid catalog ids before persistence.
- Fleet presentation keeps compatibility properties on the membership model while storage remains normalized.
- No rendered or duplicated profile snapshot is stored on memberships.
- Generated artifacts, caches, local environment files and dependency folders are excluded from the delivery archive.

## Verification

- 42 backend tests pass.
- A dedicated regression test proves the profile is the source of fleet directory data.
- All seven locale bundles pass completeness checks.
- The production frontend build succeeds.
- A fresh Alembic migration reaches revision `b2c3d4e5f6a7`.
