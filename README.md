# Iron Crown Fleet Hub

Small, intentionally clean fullstack foundation for the Iron Crown Fleet Hub. Current modules are the Build Manager, Fleet Announcements, a minimal Forum, a minimal Guide area, a Fleet Calendar, a connected Fleet Management module and a compact Staff Panel.

```text
backend/   FastAPI + SQLAlchemy + SQLite + cookie sessions
frontend/  Vue 3 + Vite
```

## Current scope

- `/home` as the Iron Crown Fleet Hub landing page with an expandable module showcase
- `/builds` as public Build Manager list with search and build-type filter
- `/builds/{id}` as public build detail page
- `/builds/new` as minimal build designer with six upgrade slots, upgrade-based stat calculation, weapons by arc and special crew
- `/register` as public user registration with improved account/fleet application UX
- `/login` as minimal session login
- `/profile` as protected profile page with password change, personal fleet status and links into fleet management
- `/profile/builds` as personal build management for own builds
- `/groups` as public announcement board with search, focus filter and rate-span filter
- `/groups/{id}` as public announcement detail page
- `/groups/new` as protected announcement creation
- `/profile/groups` as personal fleet announcement for own fleet announcements
- `/forum` and `/forum/new` as a minimal file-backed discussion board
- `/calendar` as public fleet month calendar with category filter and selected-day agenda
- `/calendar/new` as staff-only appointment creation for admins and moderators
- `/guides` and `/guides/new` as a minimal file- and build-backed guide module
- `/files` API for shared uploads used by Forum and Guides
- `/admin` as protected staff panel for admins and moderators
- `/fleets` as public fleet overview with application actions for signed-in users
- `/fleets/manage` as protected fleet-leadership workspace for profile, applications and member directory
- Admin/moderator tab for deleting builds
- Admin-only moderator creation tab
- Passwords are stored with salted PBKDF2-SHA256 hashes
- Sessions use opaque HttpOnly cookies stored server-side in SQLite, no JWT
- Ship catalog is seeded in the backend
- Item/slot catalog is seeded in the backend and loaded by the frontend
- Data is stored in SQLite with the main prototype schema normalized toward 3NF; see `docs/DATABASE_SCHEMA.md`
- UI localization is validated through `frontend/src/locales`: DE / EN / FR / ES / PT / RU / CN all expose the same key set and the locale check now rejects unapproved English fallback strings

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
http://127.0.0.1:8000/api/forum/threads
http://127.0.0.1:8000/api/calendar/events
http://127.0.0.1:8000/api/guides
http://127.0.0.1:8000/api/files
http://127.0.0.1:8000/api/fleets
http://127.0.0.1:8000/api/fleets/memberships/me
http://127.0.0.1:8000/api/admin/builds
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

The dev script already binds Vite to `0.0.0.0:5173`, so do not pass positional host/port values. For local-only binding, use `npm run dev:local`.

Frontend:

```text
http://127.0.0.1:5173/home
http://127.0.0.1:5173/builds
http://127.0.0.1:5173/groups
http://127.0.0.1:5173/forum
http://127.0.0.1:5173/calendar
http://127.0.0.1:5173/fleets
http://127.0.0.1:5173/fleets/manage
http://127.0.0.1:5173/guides
http://127.0.0.1:5173/register
http://127.0.0.1:5173/login
http://127.0.0.1:5173/profile
http://127.0.0.1:5173/admin
```

## Latest update

- Guides can now reference existing website Builds through a dedicated dropdown in the guide editor.
- Selected Builds can either be linked as general guide references or inserted inline into the body with `[[build:id|layout]]` tokens.
- Inline Build cards are server-validated against the guide's linked Build references, matching the existing file-embed validation model.
- Guide detail pages and live previews render linked Builds as enterprise-style cards and keep non-inline Build links in a dedicated reference section.
- Documentation added in `docs/GUIDE_BUILD_EMBEDS.md`; locale coverage remains complete through `npm run check:locales`.

## Previous update

- Full locale hardening pass: all supported languages now pass key coverage and unapproved-English-fallback validation through `npm run check:locales`.
- Enterprise UI pass added global design-token aliases, stronger responsive breakpoints, mobile/touch target rules, scrollable navigation groups and tighter scaling for calendar/filter/management layouts.
- Registration and shared forms now use more distinct elevated input surfaces, stronger focus rings and clearer responsive stacking.
- Documentation added for localization coverage in `docs/LOCALIZATION.md` and expanded responsive UI guidance in `docs/UI_UX_NOTES.md`.

## Previous update

- Registration UI refreshed with clearer two-step structure, stronger input contrast, persistent helper text and optional fleet application note.
- Locale coverage completed for the registration/profile layer across DE / EN / FR / ES / PT / RU / CN, with English still merged as the canonical fallback for every feature module.
- Fresh seeds now include two mock Guides and two mock Forum threads with local SVG ship/convoy images embedded through the real upload attachment pipeline.
- Backend schema cleanup moved public profile data into `user_profiles` and build option modifiers into `build_item_effects`, removing the major prototype-era transitive/serialized fields from new databases.
- Official fleet display is now centralized by `user_profiles.primary_fleet_membership_id`, so registration applications, fleet approvals and the profile all read the same membership row.
- Documentation added under `docs/` for architecture, UI/UX conventions and schema normalization.

## Previous update

- Fleet module connected end-to-end across registration, profile, public fleet overview and fleet leadership management.
- `/api/fleets/memberships/me` exposes the signed-in user's official fleet applications and memberships for frontend status displays.
- `/fleets` now lets authenticated users apply to individual fleets directly from the public list, including an optional note for fleet leadership.
- `/profile` now shows official fleet applications/memberships separately from the free-text profile field and links to fleet browsing or management.
- `/fleets/manage` now has dedicated tabs for fleet profile, pending applications and a searchable/filterable member directory.
- Third cleanup pass kept the implementation in the existing design system, validated build/API smoke paths and excludes generated artifacts from the package.

## Previous update

- Frontend dev startup is now explicit and Windows-friendly: `npm run dev` binds Vite to `0.0.0.0:5173`, `npm run dev:local` binds to `127.0.0.1:5173`, and the Vite config also declares the default host/port.
- Fleet Calendar prototype added with a Windows-style month grid, selected-day agenda and event-type filter.
- Backend now exposes `/api/calendar/events` with public reads and staff-only create/update/delete operations for admins and moderators.
- New staff form `/calendar/new` follows the existing sectioned form style for title, type, location, timing and operational notes.
- Demo calendar events are seeded for fresh databases so the calendar has immediate content after reset.
- Home showcase, navbar and locale layers now include the Fleet Calendar module.

## Previous update

- UI foundation refreshed with a calmer dark visual system, stronger spacing rhythm, card hierarchy and higher-contrast typography.
- Main navigation is grouped into brand, primary modules, account links, locale controls and session actions for clearer scanning.
- List filters were restyled as dedicated task panels with clearer search/select affordances, focus states and responsive stacking.
- The main container now uses a stable max-width shell and softer page surfaces instead of the earlier wireframe-style borders.
- `frontend/src/styles/main.css` was reorganized from an accumulated override file into a smaller design-system-oriented stylesheet.
- Frontend build tooling was updated to Vite 8 / Vue plugin 6; full `npm audit` now reports no vulnerabilities.

## Previous update

- Forum posts and Guides now render uploaded files as inline embeds instead of only listing them: images/GIFs/SVGs, videos, PDFs and TXT files are displayed directly in the content card, while unsupported file types remain available as openable links.
- Frontend file URL handling now resolves backend-hosted `/uploads/...` URLs correctly when the API is served from another origin via `VITE_API_BASE_URL`.
- The Vite dev server now proxies `/uploads` to the FastAPI backend, so local media previews work alongside the existing `/api` proxy.

## Previous update

- Frontend localization was split from one large `src/locales/index.js` file into config, runtime utilities, feature/domain message layers and option glossaries. The public `useLocale` API remains unchanged.
- Frontend API services now share one query-string helper instead of duplicating URL parameter code per module.
- Build tooling dependencies were moved to `devDependencies`; production audit via `npm audit --omit=dev` reports no vulnerabilities after the cleanup.
- Generated `__pycache__`, `node_modules` and `dist` artifacts are excluded from the packaged repo.

## Earlier update

- Build Manager now supports a fifth unlockable upgrade slot plus ship-specific sixth upgrade slot. Slot 5 is locked until an unlock upgrade such as Structural Expansion is selected in slots 1-4; slot 6 is only available on ships marked with an extra upgrade slot. Expansion debuffs are included in validation and display.
- Upgrade stat modifiers are seeded and aggregated into `ship_stats`, including buffs, debuffs, effective crew capacity/minimum and warnings.
- Backend file module stores uploaded GIF, MP4, JPEG, PNG, WebP, WebM, MOV, PDF and TXT files under `UPLOAD_DIR` and serves them through `/uploads`.
- Minimal Forum and Guide modules use the shared file module for embedded attachments.

## Earlier cleanup

- Group-rate logic corrected for Ship-of-the-Line rates: rate 1 is strongest, rate 7 is lightest.
- Minimum rate now means “that rate or better”, so a group requiring rate 4 allows 1–4 and blocks 5–7.
- Optional strongest/maximum-rate cap added; together with minimum/weakest rate it forms a valid span, e.g. 2–4.
- `/groups` now includes a rate-span filter in addition to search and focus.
- Group locale keys are filled for DE / EN / FR / ES / PT / RU / CN, with EN kept as safe canonical fallback.
- Spring-clean pass: generated caches/local DB removed from the packaged ZIP and imports/syntax verified.

## Staff Panel operations

The staff panel now covers day-to-day moderator/admin work in one place:

- calendar operations for upcoming fleet appointments
- quick actions for new calendar entries, forum threads and guides
- content moderation for forum threads, guides and fleet announcements
- build cleanup and admin-only moderator account creation

Admins and moderators can open `/admin`; regular users are redirected to login.

## Fleet management prototype

This build adds a first vertical slice for the planned fleet structure:

- Ten seeded fleets with focus areas such as trade, faction fleets, port battle, training, farming, recon and support.
- Users can select one of the known fleets during registration. This creates a pending fleet membership claim.
- Fleet leadership roles are scoped to a fleet rather than being global app roles:
  - `fleet_admiral`
  - `fleet_lieutenant`
  - `member`
- Fleet admirals and lieutenants can open `/fleets/manage` to maintain their fleet description, standing orders and member statuses.
- Administrators can manage all fleets and can promote approved members into fleet leadership roles from the same management UI.

The public overview is available at `/fleets`.


## Inline media embeds

Forum posts and guides now support explicit inline placement for uploaded files via markers such as `[[file:123|large]]`. The UI inserts these markers for users from the upload panel, renders a live preview, and leaves unused files as normal attachments. See `docs/INLINE_MEDIA_EMBEDS.md` for syntax and validation rules.
