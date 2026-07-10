# Database schema and 3NF review

Release 0.17.0 normalizes the authorization, fleet organization and Build Designer catalog relations that were still carrying duplicated codes or compound text values. The migration is additive/transitional where necessary and preserves existing primary keys and user-created content.

## Authorization catalogs

Site, fleet and squad roles are stored once in definition tables:

```text
site_roles(id, code, label, rank, is_staff, can_manage_system)
fleet_roles(id, code, label, rank, is_leadership, can_manage_fleet, can_manage_members)
squad_roles(id, code, label, rank, can_manage_roster, can_manage_events)
```

Assignments reference those rows:

```text
users.site_role_id -> site_roles.id
fleet_memberships.fleet_role_id -> fleet_roles.id
squad_members.squad_role_id -> squad_roles.id
```

The role code, display label, authority rank and capabilities therefore have one source of truth. Compatibility properties still expose `user.role`, `membership.role` and `squad_member.role` to existing API schemas without persisting those values twice.

## Account and fleet separation

`users` stores authentication and account state only:

```text
users(id, username, password_hash, site_role_id, is_active, created_at, updated_at)
```

Public profile data remains in `user_profiles`. Official fleet membership is derived from `fleet_memberships`; the former `primary_fleet_membership_id` pointer has been removed. A registration request contains only account-approval data. Fleet application fields are no longer duplicated in `registration_requests`.

The optional `user_profiles.external_fleet_name` field is free-text information for a user who is not connected to the official fleet. Once an official membership exists, the displayed fleet name, status and role are derived from the membership relation.

## Fleet organization

```text
fleets
fleet_memberships(fleet_id, user_id, fleet_role_id, status, ...)
fleet_membership_ship_preferences(fleet_membership_id, ship_name, sort_order)
squads(fleet_id, ...)
squad_members(squad_id, fleet_membership_id, squad_role_id, ...)
fleet_events(squad_id nullable, ...)
```

Preferred ships are individual rows rather than a comma-separated column. Squad membership references an active fleet membership rather than repeating user and fleet facts.

## Build Designer catalog

The previous serialized ship layout and slot lists are normalized into:

```text
weapon_classes(id, code, label, rank)
weapon_slot_types(id, code, label, sort_order)
ship_weapon_mounts(ship_id, slot_type_id, capacity, max_weapon_class_id, max_caliber_inches)
build_item_option_slot_types(option_id, slot_type_id)
build_item_options(..., weapon_class_id, weapon_caliber_inches)
```

Weapon eligibility is calculated from the selected ship mount, allowed slot type and normalized Light/Medium/Heavy class. Mortars use their dedicated slot and caliber ceiling. A derived ship-to-option eligibility cache is intentionally not persisted, avoiding update anomalies when either a ship mount or weapon definition changes.

Build selections remain in `build_slots`, and option stat modifiers remain normalized in `build_item_effects`.

## Other normalized relationships

- Guide-to-Build links: `guide_build_references`
- Guide/file links: `guide_attachments`
- Forum/file links: `forum_post_attachments`
- Squad calendar scope: nullable `fleet_events.squad_id`
- New Captain Guide sections/resources: `newcomer_guide_blocks`, `newcomer_guide_resources`

## Integrity and migration policy

Alembic revision `7e4c9b2a1f60` performs the 0.17.0 conversion. It backfills role definitions and foreign keys before removing legacy role-code columns, splits preferred ships into rows, converts ship weapon layouts into mount rows and removes obsolete registration fields.

The migration does **not** recreate PostgreSQL or its volume. Deployment uses:

```bash
sudo ./update.sh --migrate --seed
```

`--migrate` applies the intended schema conversion. `--seed` synchronizes role/catalog definitions, official starter content and the New Captain progression path. It does not reset the database.

## Scope of the 3NF statement

The relations changed in this release satisfy the practical 3NF goals of the application: non-key facts depend on their table key, role/catalog facts are not copied into assignments, and multi-valued attributes use child/join tables. User-authored prose and deliberate historical snapshots remain text by design; they are not treated as relational catalog facts.
