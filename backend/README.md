# Backend - WoSB Community Hub

Minimal FastAPI prototype with SQLAlchemy, SQLite, password hashing, registration, profiles, roles, cookie sessions, builds and groups.

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
GET    /api/groups
POST   /api/groups
GET    /api/groups/mine
GET    /api/groups/{id}
POST   /api/groups/{id}/join
POST   /api/groups/{id}/close
GET    /api/admin/builds
DELETE /api/admin/builds/{id}
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

Build data is normalized toward 3NF:

```text
users
auth_sessions
ships
builds
build_item_categories
build_item_options
build_slots
groups
group_members
```

`builds` contains no repeated slot columns and no JSON inventory lists. Loadout elements live in `build_slots` and reference `build_item_options`. Quantities are stored only on slots where they are meaningful.

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
src/app/db/seeds/manager.py
```

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
