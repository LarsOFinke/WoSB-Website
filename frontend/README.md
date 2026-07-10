# Blackwater Mercenaries Hub Frontend

Vue 3 + Vite frontend for Blackwater Mercenaries Hub.

## Mandatory environment

The frontend refuses to run or build without `frontend/.env`.

```bash
cp .env.example .env
```

Required value:

```env
VITE_API_BASE_URL=/api
```

For same-domain reverse proxy deployment, `/api` is correct. For a separate backend origin, set the full origin plus API prefix.

## Start

```bash
npm install
npm run dev
```

`npm run dev` uses the versioned settings from `config/dev-server.json` (`0.0.0.0:5173` by default for LAN testing).

## Access model

Public:

```text
/                 fleet portal/home
/login            sign in
/register         registration
/builds           public build catalog
/builds/:id       public build detail
```

Login required:

```text
/profile          account and fleet profile
/profile/builds   personal builds
/profile/groups   personal groups
/builds/new       build editor
/guides           guides
/groups           group search
/calendar         fleet calendar
/forum            forum
/fleets           fleet management
```

Staff required:

```text
/admin            staff workspace
/calendar/new     event creation
```

## Feature architecture

The frontend mirrors the backend's domain structure:

- `src/modules/<domain>/pages` — route-level screens.
- `src/modules/<domain>/api` — thin API adapters.
- `src/modules/<domain>/routes.js` — lazy routes and access metadata.
- `src/shared/api` — shared HTTP/query infrastructure.
- `src/core` — application shell, navigation and reusable workspace components.

See `../docs/FRONTEND_ARCHITECTURE.md` for the full conventions.

## Localization and build validation

```bash
npm run check:locales
npm run build
npm audit --omit=dev
find src -name '*.js' -print0 | xargs -0 -n1 node --check
```

The locale check verifies equal EN, DE, FR, ES, PT, RU and CN coverage and rejects unintended fallback strings.

## Rich content

Guides and forum content can embed uploaded files with `[[file:id|size]]`. Guides can embed linked builds with `[[build:id|layout]]`. UI panels insert these tokens; backend services validate them.
