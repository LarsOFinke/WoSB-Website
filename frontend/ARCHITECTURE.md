# Frontend architecture

The frontend is organized by feature module. Each module may expose the following layers:

```text
src/modules/<feature>/
├── api/          HTTP transport and endpoint contracts
├── domain/       Pure business, mapping, filtering and presentation rules
├── composables/  Stateful use-cases and page models
├── components/   Reusable visual building blocks
└── pages/        Route-level composition and markup
```

## Dependency direction

The intended dependency flow is:

```text
page -> composable -> domain
                   -> api
page -> component
```

Pages must not call API modules directly or own asynchronous workflows. They bind a page model to route-level markup and compose components. This boundary applies to every route page and is enforced repository-wide by `pageResponsibilityBoundaries.test.mjs` and `scripts/check_repository.py`.

Domain modules are framework-independent wherever practical. They receive their data and collaborators as arguments, return values without side effects, and can be tested with Node's built-in test runner.

Composables coordinate Vue state, lifecycle hooks, API calls and user-facing success/error state. A composable may combine smaller feature composables, as `useAdminWorkspace` and `useBuildDesigner` do.

API modules contain transport concerns only. File type policy is therefore kept in `src/modules/files/fileTypes.js` rather than coupled to file endpoints.

Executable JavaScript modules are capped at 420 lines by `scripts/check_repository.py` and should normally split at 300–400 lines along these dependency boundaries. Locale message modules and `src/locales/autoLocalizationCatalog.js` are declarative exceptions; executable localization behavior remains in the small `autoLocalization.js` module.

## Global style layers

The shared global cascade is loaded from `src/styles/global/index.js` as eight numerically ordered CSS files. The manifest uses JavaScript imports rather than nested CSS `@import`: an earlier `@import` split changed production extraction and caused visible drift. The import order is an architecture contract, every layer is capped at 75 KB and 3,500 lines, and total frontend source CSS remains below 400 KB. Feature-local styles stay beside their owning module. See `docs/reference/CSS_ARCHITECTURE.md`.

## Locale delivery

The editable translation sources live in `src/locales/messages/`. Before development, tests and production builds, `scripts/generate-locales.mjs` compiles them into one ignored runtime module per locale under `src/locales/generated/`.

English is the synchronous fallback in the application entry path. Every other locale is loaded through a dynamic import before it becomes active. This keeps untranslated keys safe, prevents mixed-language rendering during a switch and avoids shipping all seven languages on the first visit. Generated locale modules must not be edited or committed.

## Extension guide

When adding a page capability:

1. Put deterministic transformations, validation and payload mapping in `domain/`.
2. Put remote calls and state transitions in a dedicated composable.
3. Extract repeated visual structures into a component.
4. Keep the page script limited to imports, props and page-model binding.
5. Add focused domain tests and retain a route-level build check.

This is a pragmatic boundary rather than a requirement to create a file for every small function. Simple, local display expressions can remain in the page template when extracting them would make navigation harder.
