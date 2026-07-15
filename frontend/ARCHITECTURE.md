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

Pages must not call API modules directly or own asynchronous workflows. They bind a page model to route-level markup and compose components.

Domain modules are framework-independent wherever practical. They receive their data and collaborators as arguments, return values without side effects, and can be tested with Node's built-in test runner.

Composables coordinate Vue state, lifecycle hooks, API calls and user-facing success/error state. A composable may combine smaller feature composables, as `useAdminWorkspace` and `useBuildDesigner` do.

API modules contain transport concerns only. File type policy is therefore kept in `src/modules/files/fileTypes.js` rather than coupled to file endpoints.

## Extension guide

When adding a page capability:

1. Put deterministic transformations, validation and payload mapping in `domain/`.
2. Put remote calls and state transitions in a dedicated composable.
3. Extract repeated visual structures into a component.
4. Keep the page script limited to imports, props and page-model binding.
5. Add focused domain tests and retain a route-level build check.

This is a pragmatic boundary rather than a requirement to create a file for every small function. Simple, local display expressions can remain in the page template when extracting them would make navigation harder.
