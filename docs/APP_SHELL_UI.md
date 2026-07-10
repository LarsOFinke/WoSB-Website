# App Shell and Enterprise UI Overhaul

The frontend uses a two-level, role-aware navigation model:

1. **Topbar** for brand, public/member primary routes, language and account actions.
2. **Left sidebar** for the complete workspace route set available to the current session.

This keeps the header focused as the project grows and leaves the module list vertically expandable without turning the top navigation into a crowded row.

## Topbar

The topbar order is intentionally fixed:

1. Product brand and mobile menu trigger
2. Primary public/member navigation
3. Language selector
4. Session identity and logout, or login/register actions

For signed-in users, the account capsule links to the profile and displays identity plus role. Personal builds, personal groups and fleet management stay in their owning workspaces instead of overloading the topbar.

The standalone username display was removed to reduce visual clutter. The username/display name now travels with the profile link, which keeps identity and destination connected.

## Sidebar

Guest sidebar routes:

- Home
- Builds

Authenticated sidebar routes additionally include:

- Guides
- Group Search
- Calendar
- Forum
- Fleet Management
- Staff Panel for staff users

The former “Announcements” module is labelled as **Group Search** in the UI. This better reflects the intended usage as a board for finding and coordinating group activities.

The sidebar can be collapsed on desktop and opens as an off-canvas drawer on tablet/mobile.

## Responsive behavior

The app shell uses CSS grid on desktop:

```text
[topbar topbar]
[sidebar main]
[footer footer]
```

Below tablet width, the sidebar becomes a fixed off-canvas drawer with a scrim. The main content keeps the same routes and functionality; only presentation changes. This avoids a separate mobile product surface and keeps all capabilities available on small devices.

## Implementation notes

- Shell state is composed in `src/core/components/AppNavbar.vue` and managed by `src/core/composables/useAppShell.js`.
- Sidebar collapse preference is stored in `localStorage` under `rbf-hub.sidebar.collapsed` (with automatic migration from the legacy key).
- The body receives `sidebar-collapsed` and `mobile-sidebar-open` classes for layout state.
- The visual shell, responsive rules and enterprise polish are centralized in `src/styles/main.css` under `Enterprise app shell overhaul`.

## UI rules for future modules

- Add new primary modules to the sidebar.
- Add authenticated operational areas to the topbar only if they are account/staff-level destinations.
- Keep language selection near the brand so it remains discoverable without competing with operational actions.
- Keep controls touch-safe at mobile sizes.
- Prefer existing surface, form, filter and card tokens before adding one-off styling.
- Keep labels visible and focus indicators strong.
