# Frontend design and CSS quality standard

The global UI cascade is intentionally small, ordered, and boring. It is loaded from
`frontend/src/styles/global/index.js`; CSS `@import` is forbidden because earlier
bundler extraction changed cascade order in production.

## Global cascade groups

The filename states both cascade position and responsibility:

1. `00-tokens.css` — design tokens and compatibility variables; the only global `:root`
2. `10`–`24-foundation-*.css` — one named primitive family per file
3. `30`–`38-layout-*.css` — base, calendar, staff, fleet, registration and rich-content layouts
4. `40`–`49-shell-*.css` — application shell and explicitly named workspace shells
5. `50`–`56-navigation/portal-*.css` — navigation and public portal surfaces
6. `60`–`68-domain-*.css` — explicitly named cross-route domain contracts
7. `70`–`76-operations-*.css` — security, build and member operations

The numeric order is the cascade contract. Add a rule to the narrowest existing layer; do not
append unrelated fixes to the final file. A new layer requires a repository-check update and an
architecture note.

Integration and domain workspaces are deliberately not a final global layer. Their styles live
with their owner:

- `modules/admin/styles/adminWebhook*.css` — webhook configuration, editor, delivery and history
- `modules/admin/styles/adminDiscord*.css` — Discord webhook and broadcast surfaces
- `modules/admin/styles/adminDatabaseBackups.css` and `adminRaidHelper.css` — isolated operations
- `modules/admin/styles/staffWorkspace*.css` — shell, overview and responsive staff behavior
- `modules/builds/styles/buildWorkspace.css` — build designer and build detail presentation
- `modules/fleet/styles/fleetHierarchy.css` — protected fleet hierarchy
- `modules/guides/styles/guide*.css` — foundation, listing, reader, editor and responsive behavior
- `modules/forum/styles/forumReplies.css` — reply moderation
- `shared/styles/discovery.css` — the shared build/guide discovery interaction

## Feature-local styles

Large, self-contained workspaces may keep a stylesheet beside the module. Feature styles must be
imported by their owning component or page model, must not redefine global tokens, and should use
a feature prefix (`staff-`, `fleet-`, `guide-`, and so on).

## KISS and responsibility boundaries

- Global CSS owns tokens, primitives, reusable layout and the application shell. A route-specific
  selector belongs to its module, even when several pages inside that module use it.
- Centralize stable decisions, not coincidental similarities. Fonts, colors, spacing and shared
  workspace frames are tokens or primitives; a one-off three-property card does not justify a
  new global abstraction.
- A component class has one visual responsibility. Compose an existing primitive in markup
  instead of copying its declarations into a feature stylesheet.
- Later overrides are not a variant system. Use an explicit modifier or replace the earlier rule;
  contradictory declarations at the same media-query context are technical debt.
- Prefer deletion and composition over another cascade layer. New files should follow a module
  boundary and be imported by their owner.

Run `npm run analyze:css` to list repeated selector contexts, identical declaration sets and
same-rule overrides. The report is diagnostic: repeated selectors can be intentional state or
responsive refinement, so each candidate must be evaluated in its cascade context before merging.

## Rules

- Prefer design tokens over repeated literals.
- Prefer one component class over selector chains and `!important`.
- Keep specificity low; state belongs in explicit modifier classes or data attributes.
- Responsive rules stay beside the selector they adapt when practical.
- Do not use CSS `@import`, inline base64 assets, or unscoped element overrides in feature files.
- Preserve keyboard focus and reduced-motion behavior when changing visuals.
- Never hide root-level horizontal overflow. Fix the component or give the owning data surface an
  explicit horizontal scroll container.
- Run `npm test` and `python3 scripts/check_repository.py --strict-tree` after structural changes.

Repository gates cap every stylesheet at 420 lines, keep total frontend CSS below 400 KB,
enforce one token root, and verify numeric manifest order. The 420-line hard gate leaves a small
transition margin around the preferred 300–400-line responsibility size.

## Specificity budget

The global cascade is capped at 28 `!important` declarations. A new exception must replace or remove an existing one rather than growing the budget. The standalone CSS audit reports the count per file.

## Responsive contract

Responsive rules use only the following maximum-width thresholds:

| Breakpoint | Intended transition |
| --- | --- |
| `1480px` | exceptional wide topbar compression only |
| `1320px` | wide shell and multi-column workspace reduction |
| `1180px` | desktop workspace columns become compact |
| `1050px` | tablet landscape and application drawer transition |
| `900px` | tablet portrait and data-card layouts |
| `720px` | phone navigation and single-column forms |
| `620px` | compact phone data presentation |
| `480px` | narrow-phone finishing adjustments |

Do not introduce a nearby breakpoint for a single component. Prefer intrinsic grids using
`auto-fit`, `minmax()`, `clamp()` and `min-width: 0`. If a genuinely new threshold is required,
update this table and `frontend/scripts/check-responsive-css.mjs` in the same change.

The responsive source check protects the breakpoint contract above. Manual layout
review covers widths `320`, `375`, `430`, `720`, `768`, `1024` and `1440` pixels.
The automated Playwright suite currently exercises the accessible mobile navigation
at `390px` in real Chromium, in addition to desktop navigation and critical forms.
Public, member and administrative routes must not make the document root wider than
its viewport. Wide tables may scroll inside a labelled local container.

## Legibility and touch interaction

- Root text remains 16px at every viewport; density is reduced through layout, not global scaling.
- Application text must not be smaller than `0.75rem` or 12px.
- Interactive controls use `--touch-target` (`2.75rem`) as their coarse-pointer minimum.
- Small artwork may be smaller, but its interactive parent must retain the full target.
- Mobile layouts may reorder or collapse secondary information, but must not remove information
  needed to understand a record or make a decision.
- Drawers and full-height surfaces use `100vh` as fallback followed by `100dvh`.

## Accessibility and interaction states

- Native interactive elements are preferred. A non-native clickable element requires a suitable
  role, keyboard activation for Enter and Space, and a visible focus state.
- `:focus-visible` must remain visible and must not be clipped by an ancestor solely for cosmetic
  reasons.
- Hover may enhance an element but cannot be the only indication of state or availability.
- Motion must respect `prefers-reduced-motion`; touch layouts must not depend on hover.
- Color cannot be the sole carrier of success, warning, selection or error state.
- `forced-colors` and real-device contrast checks are part of the manual release review even when
  the automated CSS gate is green.

## Color and surface system

Repeated colors belong in `00-tokens.css` under semantic names such as line, surface, text,
accent, success or danger. Feature-specific artwork may use local literals, but the repository
maintains a ratcheting literal budget in `check-responsive-css.mjs`; new work must not increase it.
This keeps future theme and contrast work bounded without forcing every one-off illustration into
the global token API.

Typography uses semantic stacks (`--font-editorial`, `--font-mono`) rather than repeating fallback
lists. `--font-display` remains the product-level display choice; do not silently substitute it for
editorial content merely because both are headings.

## Definition of done for frontend design changes

1. Test the affected flow with keyboard only and verify visible focus and logical order.
2. Check 320, 375, 430, 720, 768, 1024 and 1440px widths; include long translated content.
3. Confirm no document-level horizontal overflow and no clipped focused element.
4. Confirm important metadata and actions remain available on phones.
5. Run `(cd frontend && npm test && npm run build)`,
   `python3 scripts/audit_css.py` and
   `python3 scripts/check_repository.py --strict-tree` from the repository root.
6. For release-affecting layout changes, run `npm run test:browser` from
   `frontend/` in an environment with the supported Playwright Chromium binary.
7. Manually sample current Chrome/Chromium, Firefox and Safari/iOS before release. Automated
   Chromium coverage does not replace engine- and device-specific review.
