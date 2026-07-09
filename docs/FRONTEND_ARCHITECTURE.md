# Frontend Architecture

## Structure

```text
frontend/src
├── core/components       Shell and reusable visual building blocks
├── core/composables      Reusable reactive logic
├── core/navigation       Navigation definitions
├── locales               Locale runtime and message packs
├── pages                 Route-level feature screens
├── router                Route table and guards
├── services              API adapters
└── styles/main.css       Global design system and responsive shell rules
```

## App shell

The app shell is split into small pieces:

- `AppNavbar.vue` composes shell navigation.
- `AppTopbar.vue` owns account/language/brand actions.
- `AppSidebar.vue` owns workspace navigation.
- `useAppShell.js` owns mobile sidebar and collapsed-state behavior.
- `workspaceLinks.js` is the single source for sidebar ordering.

This keeps future navigation additions from turning the shell into another large component.

## API services

Feature services in `frontend/src/services` should stay thin:

- build URL/query parameters;
- call `apiFetch`;
- return API data;
- avoid view formatting or domain decisions.

## Localization

All visible UI text should come from `useLocale().t(...)` unless it is user-generated content or catalog/game data. Run before shipping:

```bash
npm run check:locales
```

The locale check verifies equal key coverage and blocks unintended English fallback text in non-English packs.

## Responsive UI rules

- Keep page content inside the app shell; do not create page-specific full viewport hacks.
- Prefer existing panel/card/form classes before adding page-specific CSS.
- Test at common breakpoints: 1280, 1024, 768, 560 and 420 px.
- Mobile navigation should use the off-canvas sidebar, not an overfilled topbar.

## Rich content rules

- File embeds use `[[file:id|small|medium|large|full]]` inserted by UI helpers.
- Build embeds use `[[build:id|compact|card|full]]` inserted by UI helpers.
- Renderer components must tolerate unknown/deleted references and avoid breaking page layout.
