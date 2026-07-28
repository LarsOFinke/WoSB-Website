# CSS architecture

The global UI cascade is intentionally small, ordered, and boring. It is loaded from
`frontend/src/styles/global/index.js`; CSS `@import` is forbidden because earlier
bundler extraction changed cascade order in production.

## Global layers

1. `00-tokens.css` — design tokens and compatibility variables. It is the only global `:root`.
2. `10-foundation.css` — reset, typography, primitive controls, and accessibility defaults.
3. `20-layout.css` — shared containers, grids, spacing utilities, and generic responsive rules.
4. `30-shell.css` — application shell, headers, shared panels, and route framing.
5. `40-navigation-and-portal.css` — identity, navigation, public portal, and entry flows.
6. `50-domain-workspaces.css` — fleet, builds, guides, forum, calendar, and profile workspaces.
7. `60-operations.css` — staff operations, security views, logs, and administrative controls.
8. `70-integrations.css` — webhooks, broadcasts, backups, editor overlays, and later compatibility fixes.

The numeric order is the cascade contract. Add a rule to the narrowest existing layer; do not
append unrelated fixes to the final file. A new layer requires a repository-check update and an
architecture note.

## Feature-local styles

Large, self-contained workspaces may keep a stylesheet beside the module. Feature styles must be
imported by their owning component or page model, must not redefine global tokens, and should use
a feature prefix (`staff-`, `fleet-`, `guide-`, and so on).

## Rules

- Prefer design tokens over repeated literals.
- Prefer one component class over selector chains and `!important`.
- Keep specificity low; state belongs in explicit modifier classes or data attributes.
- Responsive rules stay beside the selector they adapt when practical.
- Do not use CSS `@import`, inline base64 assets, or unscoped element overrides in feature files.
- Preserve keyboard focus and reduced-motion behavior when changing visuals.
- Run `npm test` and `python scripts/check_repository.py --strict-tree` after structural changes.

Repository gates cap each global layer at 75 KB and 3,500 lines, keep total frontend CSS below
400 KB, enforce one token root, and verify the import order.

## Specificity budget

The global cascade is capped at 28 `!important` declarations. A new exception must replace or remove an existing one rather than growing the budget. The standalone CSS audit reports the count per file.
