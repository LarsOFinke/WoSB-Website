# Frontend

Vue 3 + Vite frontend for Iron Crown Fleet Hub.

## Start

```bash
npm install
npm run dev
```

`npm run dev` already binds to `0.0.0.0:5173`. Use `npm run dev:local` for `127.0.0.1:5173`.

## Routes

```text
/home
/builds
/guides
/groups
/calendar
/forum
/fleets
/profile
/admin
```

Feature detail/create routes live under those module roots.

## Layout architecture

The app shell is split into:

- `src/core/components/AppNavbar.vue` — shell composition.
- `src/core/components/AppTopbar.vue` — brand, languages, account links and session actions.
- `src/core/components/AppSidebar.vue` — workspace navigation.
- `src/core/composables/useAppShell.js` — sidebar/mobile state.
- `src/core/navigation/workspaceLinks.js` — single source for sidebar order.

## Localization

Run after UI text changes:

```bash
npm run check:locales
```

The check verifies that EN, DE, FR, ES, PT, RU and CN expose the same key set and that non-English locales do not accidentally surface English fallback UI strings.

## Build validation

```bash
npm run check:locales
npm run build
npm audit --omit=dev
find src -name '*.js' -print0 | xargs -0 -n1 node --check
```

## Rich content

Guides and Forum content can embed uploaded files with `[[file:id|size]]`. Guides can embed linked Builds with `[[build:id|layout]]`. UI panels insert these tokens for users; backend services validate them.

See `../docs/FRONTEND_ARCHITECTURE.md` for frontend conventions.


## Single Fleet Refactor

Der Flottenbereich arbeitet jetzt mit genau einer offiziellen Iron Crown Fleet. Registrierung, Profil und Flottenverwaltung referenzieren dieselbe zentrale Membership. Details stehen in `docs/SINGLE_FLEET_REFACTOR.md`.

## Build stat breakdown

Build create/detail views show base ship stats, selected upgrade modifiers and effective build values using the stat definitions returned by `/api/builds/options`.
