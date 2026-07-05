# WoSB Community Hub

Small, intentionally clean fullstack foundation for the WoSB Community Hub. The first modules are the Build Manager and a minimal Group Management area; the first protected area is a compact Staff Panel.

```text
backend/   FastAPI + SQLAlchemy + SQLite + cookie sessions
frontend/  Vue 3 + Vite
```

## Current scope

- `/home` as the WoSB Community Hub landing page with an expandable module showcase
- `/builds` as public Build Manager list with search and build-type filter
- `/builds/{id}` as public build detail page
- `/builds/new` as minimal build designer, reachable only via the button on `/builds`
- `/register` as public user registration
- `/login` as minimal session login
- `/profile` as protected minimalist profile page with password change
- `/profile/builds` as personal build management for own builds
- `/groups` as public group board with search, focus filter and rate-span filter
- `/groups/{id}` as public group detail page with join form
- `/groups/new` as protected group creation
- `/profile/groups` as personal group management for own group calls
- `/admin` as protected staff panel for admins and moderators
- Admin/moderator tab for deleting builds
- Admin-only moderator creation tab
- Passwords are stored with salted PBKDF2-SHA256 hashes
- Sessions use opaque HttpOnly cookies stored server-side in SQLite, no JWT
- Ship catalog is seeded in the backend
- Item/slot catalog is seeded in the backend and loaded by the frontend
- Builds are stored in SQLite and normalized toward 3NF
- UI localization is prepared through `frontend/src/locales`: default EN, switcher for DE / EN / FR / ES / PT / RU / CN

## Backend

```bash
cd backend
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

Change this before production through environment variables from `backend/.env.example`.

API:

```text
http://127.0.0.1:8000/api/health
http://127.0.0.1:8000/api/auth/me
http://127.0.0.1:8000/api/profile
http://127.0.0.1:8000/api/ships
http://127.0.0.1:8000/api/builds
http://127.0.0.1:8000/api/builds/options
http://127.0.0.1:8000/api/groups
http://127.0.0.1:8000/api/admin/builds
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://127.0.0.1:5173/home
http://127.0.0.1:5173/builds
http://127.0.0.1:5173/groups
http://127.0.0.1:5173/register
http://127.0.0.1:5173/login
http://127.0.0.1:5173/profile
http://127.0.0.1:5173/admin
```

## Latest cleanup

- Group-rate logic corrected for Ship-of-the-Line rates: rate 1 is strongest, rate 7 is lightest.
- Minimum rate now means “that rate or better”, so a group requiring rate 4 allows 1–4 and blocks 5–7.
- Optional strongest/maximum-rate cap added; together with minimum/weakest rate it forms a valid span, e.g. 2–4.
- `/groups` now includes a rate-span filter in addition to search and focus.
- Group locale keys are filled for DE / EN / FR / ES / PT / RU / CN, with EN kept as safe canonical fallback.
- Spring-clean pass: generated caches/local DB removed from the packaged ZIP and imports/syntax verified.
