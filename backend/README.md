# Backend - Iron Crown Fleet Hub

Minimal FastAPI prototype with SQLAlchemy, SQLite, password hashing, registration, normalized profiles, roles, cookie sessions, builds, announcements, file uploads, forum threads, guides, fleet management and fleet calendar events.

## Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
wosb-seed --reset
wosb-dev
```

Seeded admin login:

```text
admin / admin123
```

The credentials can be changed through:

```env
SEED_ADMIN_USERNAME="admin"
SEED_ADMIN_PASSWORD="admin123"
SEED_ADMIN_DISPLAY_NAME="Community Admin"
```

## Endpoints

```text
GET    /api/health
GET    /api/home
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/me
POST   /api/auth/change-password
GET    /api/profile
PUT    /api/profile
GET    /api/ships
GET    /api/builds
GET    /api/builds/options
GET    /api/builds/mine
POST   /api/builds
DELETE /api/builds/mine/{id}
GET    /api/builds/{id}
GET    /api/files
POST   /api/files
DELETE /api/files/{id}
GET    /api/forum/threads
POST   /api/forum/threads
GET    /api/forum/threads/{id}
POST   /api/forum/threads/{id}/posts
GET    /api/calendar/events
POST   /api/calendar/events
GET    /api/calendar/events/{id}
PUT    /api/calendar/events/{id}
DELETE /api/calendar/events/{id}
GET    /api/guides
POST   /api/guides
GET    /api/guides/{id}
DELETE /api/guides/{id}
GET    /api/groups
POST   /api/groups
GET    /api/groups/mine
GET    /api/groups/{id}
POST   /api/groups/{id}/join
POST   /api/groups/{id}/close
GET    /api/admin/builds
DELETE /api/admin/builds/{id}
GET    /api/fleets
GET    /api/fleets/memberships/me
GET    /api/fleets/manageable
GET    /api/fleets/{id}
GET    /api/fleets/{id}/manage
POST   /api/fleets/join
PUT    /api/fleets/{id}
PUT    /api/fleets/{id}/memberships/{membership_id}
GET    /api/admin/users
POST   /api/admin/moderators
```

## Auth

- Passwords are stored as salted PBKDF2-SHA256 hashes.
- Login creates an opaque random session token.
- Only the SHA-256 hash of the session token is stored in `auth_sessions`.
- The browser receives an HttpOnly cookie.
- No JWT is used.
- Public registration creates normal `user` accounts.
- Admins can create `moderator` accounts.
- Moderators can use the build moderation panel, but cannot create other moderators.

## Data model

Current prototype data is normalized toward 3NF:

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
groups
group_members
stored_files
forum_threads
forum_posts
forum_post_attachments
guides
guide_attachments
fleets
fleet_memberships
fleet_events
```

`builds` contains no repeated slot columns and no JSON inventory lists. Loadout elements live in `build_slots` and reference `build_item_options`. Quantities are stored only on slots where they are meaningful. Upgrade modifiers live in `build_item_effects` and are aggregated into `ship_stats` for API consumers. Public profile data lives in `user_profiles`; official fleet state lives in `fleet_memberships`, not duplicated on `users`.

## Seeds

Seeds are split by domain and orchestrated by `SeedManager`:

```text
src/app/db/seeds/users.py
src/app/db/seeds/categories.py
src/app/db/seeds/ships.py
src/app/db/seeds/sails.py
src/app/db/seeds/upgrades.py
src/app/db/seeds/lanterns.py
src/app/db/seeds/ammunition.py
src/app/db/seeds/consumables.py
src/app/db/seeds/hold_items.py
src/app/db/seeds/weapons.py
src/app/db/seeds/demo_builds.py
src/app/db/seeds/demo_groups.py
src/app/db/seeds/demo_fleets
fleet_memberships
fleet_events.py
src/app/db/seeds/manager.py
```

Uploads are written below `UPLOAD_DIR` (default `storage/uploads`) and served as `/uploads/<relative_path>`. Forum and Guide attachments only store file IDs and reuse this shared module.

Reset and seed:

```bash
wosb-seed --reset
```

## Group rate semantics

Ship-of-the-Line rates count down: `1` is strongest and `7` is lightest.

For groups:

- `min_ship_rate` means the weakest allowed rate. Example: `4` allows rates `1–4`.
- `max_ship_rate` means the strongest allowed rate. Example: `2` together with `min_ship_rate = 4` allows rates `2–4`.
- Backend join validation always enforces the span.

## Fleet calendar

`fleets
fleet_memberships
fleet_events` stores public calendar entries with title, category, optional location/description, start/end datetimes, all-day flag and owner. Reads are public; create, update and delete require `require_staff`, so both admins and moderators can manage fleet appointments. Delete is implemented as a soft cancel via `is_cancelled`.

## Additional docs

- `docs/ARCHITECTURE.md` — backend/frontend structure and permission model.
- `docs/DATABASE_SCHEMA.md` — table overview and normalization notes.
- `docs/UI_UX_NOTES.md` — form, filter and registration UX conventions.
