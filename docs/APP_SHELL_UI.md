# App Shell and Enterprise UI Overhaul

The frontend now uses a two-level navigation model:

1. **Topbar** for identity, account actions and operational shortcuts.
2. **Left sidebar** for expandable product modules and day-to-day workspace navigation.

This keeps the header focused as the project grows and leaves the module list vertically expandable without turning the top navigation into a crowded row.

## Topbar

The topbar contains:

- product brand and mobile menu trigger
- profile link
- fleet management link for signed-in users
- staff panel link for staff users
- locale selector
- current user and logout, or login/register actions

Keep the topbar limited to high-level account and operational controls. New modules should normally be added to the sidebar, not to the topbar.

## Sidebar

The sidebar contains the main workspace routes:

- Home
- Builds
- Announcements
- Forum
- Calendar
- Fleets
- Guides

Authenticated personal shortcuts are grouped separately below the primary module navigation. The sidebar can be collapsed on desktop and opens as an off-canvas drawer on tablet/mobile.

## Responsive behavior

The app shell uses CSS grid on desktop:

```text
[topbar topbar]
[sidebar main]
[footer footer]
```

Below tablet width, the sidebar becomes a fixed off-canvas drawer with a scrim. The main content keeps the same routes and functionality; only presentation changes. This avoids a separate mobile product surface and keeps all capabilities available on small devices.

## Implementation notes

- Shell state is managed in `src/core/components/AppNavbar.vue`.
- Sidebar collapse preference is stored in `localStorage` under `wosb.sidebar.collapsed`.
- The body receives `sidebar-collapsed` and `mobile-sidebar-open` classes for layout state.
- The visual shell, responsive rules and enterprise polish are centralized in `src/styles/main.css` under `Enterprise app shell overhaul`.

## UI rules for future modules

- Add new primary modules to the sidebar.
- Add authenticated operational areas to the topbar only if they are account/staff-level destinations.
- Keep controls touch-safe at mobile sizes.
- Prefer existing surface, form, filter and card tokens before adding one-off styling.
- Keep labels visible and focus indicators strong.
