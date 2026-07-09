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
