# Frontend - WoSB Community Hub

Vue 3 + Vite frontend for the minimal Community Hub prototype.

## Start

```bash
npm install
npm run dev
```

`npm run dev` already starts Vite on `0.0.0.0:5173`. Use `npm run dev:local` if you only want `127.0.0.1:5173`. Avoid `npm run dev --host 0.0.0.0 --port 5173`; depending on npm/PowerShell parsing, those values can be passed as raw positional arguments.

Routes:

```text
/home
/builds
/builds/:id
/builds/new
/register
/login
/profile
/profile/builds
/groups
/groups/:id
/groups/new
/profile/groups
/forum
/forum/new
/forum/:id
/calendar
/calendar/new
/guides
/guides/new
/guides/:id
/admin
```


## UI foundation

The UI is organized around one shared stylesheet in `src/styles/main.css` with tokenized color, spacing, radius and elevation values. The current pass focuses on:

- a structured app shell and grouped navigation
- consistent content cards and detail panels
- dedicated filter panels for list pages
- responsive grids that collapse predictably on tablet and mobile
- visible focus states and stronger text/background contrast

Keep new module styles aligned with these existing tokens before introducing new local variants.

## Fleet calendar

The Fleet Calendar lives in `src/pages/calendar/` and uses `src/services/fleetCalendar.js` for `/api/calendar/events`. Public users get a month grid plus selected-day agenda. Admins and moderators also see the `New appointment` action and can access `/calendar/new`.

Calendar styles are kept in the shared stylesheet under the Fleet calendar section and reuse the global tokens, card surfaces, filter panel and form-section patterns.

## Upload embeds

Forum posts and Guides use `src/core/components/AttachmentGallery.vue` for uploaded file previews. The component embeds images, GIFs/SVGs, videos, PDFs and TXT files inline, and falls back to a plain file link for unsupported formats.

File URLs are normalized in `src/services/files.js`. Local development proxies both `/api` and `/uploads` to FastAPI, while deployments with a full `VITE_API_BASE_URL` resolve uploaded assets to the backend origin.

## Dev server scripts

- `npm run dev` starts Vite on `0.0.0.0:5173` for LAN/device access.
- `npm run dev:local` starts Vite on `127.0.0.1:5173`.
- `npm run dev:default` keeps Vite's default CLI behavior for ad-hoc overrides.
- `npm run preview` serves the production preview on `0.0.0.0:4173`.

## Structure notes

- `src/locales/index.js` contains only the small runtime API (`useLocale`, `setLocale`, `translate`).
- `src/locales/messages/` contains layered translation data by feature/domain. English is merged first as the fallback layer; locale-specific entries override it.
- `src/locales/glossaries/` contains term replacement glossaries for catalog option names.
- `src/services/query.js` centralizes URL query-string creation so API services stay small and consistent.

Build tooling (`vite`, `@vitejs/plugin-vue`) lives in `devDependencies`; runtime dependencies stay limited to Vue and Vue Router. The UI refresh also updates the build tooling to Vite 8 / Vue plugin 6, with `npm audit` reporting no vulnerabilities.

Protected routes use the backend session cookie. `/admin` is available to admins and moderators; only admins see moderator creation. Start the backend and seed the database before logging in.

Seeded admin:

```text
admin / admin123
```
