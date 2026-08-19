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

Pages must not call API modules directly or own asynchronous workflows. They bind a page model to route-level markup and compose components. This boundary applies to every route page and is enforced repository-wide by `pageResponsibilityBoundaries.test.mjs` and `infrastructure/scripts/quality/check_repository.py`.

Domain modules are framework-independent wherever practical. They receive their data and collaborators as arguments, return values without side effects, and can be tested with Node's built-in test runner.

Browser-only presentation integration such as DOM serialization, downloads, and
print orchestration stays outside `domain/`; keep it at the owning feature boundary
or in a composable when it coordinates page state.

Composables coordinate Vue state, lifecycle hooks, API calls and user-facing success/error state. A composable may combine smaller feature composables, as `useAdminWorkspace` and `useBuildDesigner` do.

API modules contain transport concerns only. File type policy is therefore kept in `src/modules/files/fileTypes.js` rather than coupled to file endpoints.

Shared-content authoring is a staff capability. Route metadata uses
`requiresContentAuthor`, while pages and navigation use `canAuthorContent`; both resolve
to moderator or administrator in the session model. Fleet-management UI uses the same
staff threshold. These controls keep ordinary accounts in a clear read-only experience,
but Spring Security remains the authoritative mutation boundary.

Executable JavaScript modules and Vue single-file components are capped at 420 lines by `infrastructure/scripts/quality/check_repository.py` and should normally split at 300–400 lines along these dependency boundaries. Locale message modules and `src/locales/autoLocalizationCatalog.js` are declarative exceptions; executable localization behavior remains in the small `autoLocalization.js` module. Build crew and inventory fields are presentation components beneath `BuildCreatePage.vue`; Master Data workspace styling is owned by `styles/masterDataWorkspace.css` rather than its route page.

Application source remains JavaScript. `jsconfig.json` applies incremental TypeScript
checking to the Strategy Planner's document and geometry domain modules, where dynamic
persisted data makes refactoring risk highest; expand that checked boundary deliberately
as adjacent modules gain stable domain shapes.

## Global style layers

The shared global cascade is loaded from `src/styles/global/index.js` as eight numerically ordered CSS files. The manifest uses JavaScript imports rather than nested CSS `@import`: an earlier `@import` split changed production extraction and caused visible drift. The import order is an architecture contract, every layer is capped at 75 KB and 3,500 lines, and total frontend source CSS remains below 400 KB. Feature-local styles stay beside their owning module. See `docs/reference/CSS_ARCHITECTURE.md`.

## Locale delivery

The editable translation sources live in `src/locales/messages/`. Before development, tests and production builds, `scripts/generate-locales.mjs` compiles them into one ignored runtime module per locale under `src/locales/generated/`.

English is the synchronous fallback in the application entry path. Every other locale is loaded through a dynamic import before it becomes active. This keeps untranslated keys safe, prevents mixed-language rendering during a switch and avoids shipping all seven languages on the first visit. Generated locale modules must not be edited or committed.

## Strategy Planner geometry

The Strategy Planner stores normalized editable objects independently from the
uploaded chart. `strategyDocument.js` owns the versioned serialized contract and
`strategyGeometry.js` converts normalized dimensions into rendered SVG geometry.
Scaling a line, arrow, or formation changes its geometric extent without scaling
stroke weight or arrowhead legibility. A circle uses one physical diameter; the
independently sized legacy shape is an oval. Version-1 circle formations migrate
to `oval` when read, while new version-2 `circle` objects remain round.

Keep object creation in `StrategyToolbar.vue`. Properties of the selected object
belong in the inspector's selection section, while size and rotation remain in a
separate transform section. This distinction must also be preserved in responsive
and browser tests.

## New Captain Guide workspace

The onboarding route deliberately combines established interaction patterns instead
of presenting a second conventional article library:

- an Explorer-style address bar, topic navigation, reader, and status bar preserve the
  user's location without squeezing the briefing into a third preview column;
- the home view provides compact search and type refinement over scannable topic cards;
- selecting a topic opens its complete Markdown briefing and typed resources in a wide,
  readable article, with adjacent-topic navigation and a compact mobile topic picker;
- Guides, Builds, internal pages, and external references remain grouped inside their
  owning topic; and
- moderators use a separate two-pane workspace over that same content model: ordered
  structure on the left, focused section editing on the right, and collapsible resource
  cards that keep large guides manageable.

`NewcomerGuidePage.vue` remains the route orchestrator,
`useNewcomerGuidePage.js` owns loading/editing/selection state,
`NewcomerTopicExplorer.vue` owns the reader workspace, and the pure draft and
presentation rules remain under `src/modules/onboarding/domain/`. Preserve this shared
content model when extending onboarding: a new content type should become a typed topic
resource with a safe resolved target, not a parallel page-level navigation system.

## Guild Warehouse workspace

The administrator-only warehouse route follows the same page-model boundary. The page
renders spreadsheet-style filters, totals, and rows; `useWarehousePage.js` coordinates
loading and mutations; `warehouse.js` owns transport; and the domain module owns draft
validation and payload mapping. An entry belongs to one fleet and identifies its holder
as either an active fleet member or a custom operational name, never both.

The API-provided row version must accompany updates and deletes. A `409` is a real
concurrent-edit signal: keep the error visible and reload the authoritative row instead
of silently overwriting newer stock. Frontend admin guards only shape navigation; the
backend remains the authorization and membership boundary.

## Extension guide

When adding a page capability:

1. Put deterministic transformations, validation and payload mapping in `domain/`.
2. Put remote calls and state transitions in a dedicated composable.
3. Extract repeated visual structures into a component.
4. Keep the page script limited to imports, props and page-model binding.
5. Add focused domain tests and retain a route-level build check.

This is a pragmatic boundary rather than a requirement to create a file for every small function. Simple, local display expressions can remain in the page template when extracting them would make navigation harder.
