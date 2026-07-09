# Database Schema and Normalization

The schema is designed around 3NF for the current prototype scope: facts about users, profiles, fleets, memberships, build options, build effects, uploads, forum posts and guides are stored in their own tables instead of duplicating derived data across parent rows.

## Tables

```text
users
user_profiles
auth_sessions
ships
builds
build_item_categories
build_item_options
build_item_effects
build_slots
fleets
fleet_memberships
fleet_events
groups
group_members
stored_files
forum_threads
forum_posts
forum_post_attachments
guides
guide_attachments
guide_build_references
```

## 3NF-oriented changes in this pass

### User profile split

`users` now contains account/auth state only:

```text
id, username, password_hash, role, is_active, created_at, updated_at
```

Mutable public profile information moved to `user_profiles`:

```text
user_id, display_name, external_fleet_name, primary_fleet_membership_id, preferred_focus, note
```

Official fleet membership is not stored on `users`. It lives in `fleet_memberships`, which avoids redundant `fleet_id` / `fleet_name` pairs on the user account. The profile points to exactly one canonical membership through `primary_fleet_membership_id`; profile fleet name, role and status are derived from that row. Registration with a planned fleet creates the membership application and stores that pointer immediately. When fleet leadership accepts the application, the same membership row switches to `active`, so the profile changes automatically without a second free-text update.

### Build effects split

Build option modifiers are no longer stored as a JSON blob on `build_item_options`. They now live in `build_item_effects`:

```text
option_id, effect_key, effect_value
```

The API still returns `stat_effects` as a dictionary for frontend convenience, but the persisted data is normalized and queryable.

### Guide Build references

Guides link Builds through `guide_build_references` instead of copying Build names, ships or stats into the guide row:

```text
guide_build_references(guide_id, build_id, sort_order)
```

Inline markers such as `[[build:12|card]]` only control placement inside the guide body. The persisted source of truth is the join table, which keeps the schema normalized and lets Build data stay in the Build module.

### File attachments

Uploaded files are stored once in `stored_files`. Forum posts and guides reference them through join tables:

```text
forum_post_attachments(post_id, file_id, sort_order)
guide_attachments(guide_id, file_id, sort_order)
```

This avoids duplicating file metadata in content tables.

## Compatibility note

SQLite development databases from older prototype versions may still contain unused legacy columns. `create_tables()` backfills `user_profiles` from old columns when present, but new databases created from the current metadata use the normalized table shape.

For a clean schema during local development, run:

```bash
wosb-seed --reset
```

## Integrity constraints added in the production-foundation pass

Fresh schemas now include additional database-level checks for common application invariants:

- `users.role` is constrained to `user`, `moderator` or `admin`.
- `fleet_memberships.role` is constrained to member/admiral/lieutenant values.
- `fleet_memberships.status` is constrained to pending/active/inactive values.
- group status and ship rates are constrained to valid ranges.
- fleet event `end_at` must not be before `start_at`.
- build crew counts, slot indexes and slot quantities are non-negative/positive where appropriate.

These checks complement Pydantic/service validation. They are not a substitute for migrations; they make new clean schemas safer while the prototype still uses `create_all`.

## 3NF review

The current schema is 3NF-oriented for the prototype scope:

- non-key facts about users are in `user_profiles`, not duplicated in `users`;
- official fleet state is stored once in `fleet_memberships` and referenced by profile;
- build option stat effects are individual rows, not serialized JSON;
- Guide↔Build and content↔File relationships are join tables;
- demo/catalog names are not copied into dependent content rows except where a historical snapshot is intentionally useful for user-generated text.

The main remaining production task is adding a real migration layer so these constraints and future schema changes can be reviewed and applied safely.


## Admin Dashboard Update

- Registrations are now staged in `registration_requests` and must be approved by an admin before a user account is created.
- Admins can approve/reject requests in the new access review view.
- Application/request logs are persisted in `app_logs` and surfaced in the admin dashboard.
- See `docs/ADMIN_DASHBOARD.md` for the flow and operational details.


## Single Fleet Refactor

Der Flottenbereich arbeitet jetzt mit genau einer offiziellen Iron Crown Fleet. Registrierung, Profil und Flottenverwaltung referenzieren dieselbe zentrale Membership. Details stehen in `docs/SINGLE_FLEET_REFACTOR.md`.
