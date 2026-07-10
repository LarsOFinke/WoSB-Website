# Frontend Architecture

The frontend follows the same feature-oriented boundaries as the FastAPI backend. Route screens, API adapters and route declarations for a domain live together instead of being split across global `pages` and `services` directories.

## Structure

```text
frontend/src
├── core/
│   ├── components/       application shell and reusable UI building blocks
│   ├── composables/      shell-level reactive behavior
│   └── navigation/       role-aware workspace navigation
├── modules/
│   ├── accounts/         login, registration, profile and session state
│   ├── admin/            staff workspace
│   ├── builds/           build catalog, details and editor
│   ├── calendar/         fleet calendar
│   ├── fleet/            public fleet portal and fleet management
│   ├── forum/            forum screens and API adapter
│   ├── groups/           group search screens and API adapter
│   ├── guides/           guide screens and API adapter
│   ├── files/            upload API adapter
│   └── ships/            ship catalog API adapter
├── shared/
│   ├── api/              shared HTTP client and query helpers
│   └── content/          rich-content/embed utilities
├── locales/              locale runtime and message packs
├── router/               module route composition and global guards
└── styles/main.css       global design system and responsive workspace rules
```

## Domain module shape

A module owns the frontend parts of its backend domain:

```text
modules/<domain>/
├── api/                  thin endpoint adapters
├── pages/                route-level screens
├── routes.js             lazy route declarations and access metadata
└── session.js            domain state only when required
```

Not every module needs every folder. Shared behavior belongs in `core` only when it is shell-wide, or in `shared` when multiple domains consume it without owning it.

## Routing and access policy

`src/router/index.js` composes every module's `routes.js` and applies the global session guard.

Public routes:

- `/` — fleet portal/home
- `/login` and `/register`
- `/builds` and `/builds/:id`

Authenticated routes include profile, guides, groups, forum, calendar, fleet management, build creation and personal workspaces. Staff routes add `/admin` and `/calendar/new`.

The frontend guard is a user-experience boundary, not the security boundary. Matching authorization is enforced by FastAPI dependencies on the backend.

## App shell

- `AppNavbar.vue` composes the shell.
- `AppTopbar.vue` owns brand, primary navigation, locale and account actions.
- `AppSidebar.vue` owns role-aware workspace navigation.
- `useAppShell.js` owns mobile/collapsed sidebar behavior.
- `workspaceLinks.js` is the single source for sidebar ordering and visibility.
- `PageHeader.vue` and `MetricCard.vue` provide the shared professional workspace pattern used by profile, fleet and staff screens.

## API adapters

Module API adapters stay thin:

- build URLs and query parameters;
- call the shared `apiFetch` client;
- return backend contracts without view formatting;
- keep business rules in backend services or page-specific presentation logic.

Do not recreate a global `services/` directory. New endpoints belong to the module that owns the domain.

## Localization

All visible UI text should come from `useLocale().t(...)` unless it is user-generated content or catalog/game data. Run before shipping:

```bash
npm run check:locales
```

The locale check verifies equal key coverage and blocks unintended English fallback text in non-English packs.

## Responsive UI rules

- Keep page content inside the app shell; do not create page-specific viewport hacks.
- Prefer the shared workspace header, metric cards, panels and form classes.
- Test at 1280, 1024, 768, 560 and 420 px.
- Mobile navigation uses the off-canvas sidebar rather than an overfilled topbar.
- Sticky elements must never trap long forms or hide primary actions.

## Rich content rules

- File embeds use `[[file:id|small|medium|large|full]]` inserted by UI helpers.
- Build embeds use `[[build:id|compact|card|full]]` inserted by UI helpers.
- Renderer components tolerate unknown or deleted references without breaking page layout.
