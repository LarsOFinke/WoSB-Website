# UI/UX Release 0.15

## Public information architecture

The anonymous application shell exposes two content destinations:

- `/` — localized landing page
- `/fleet` — compact public fleet identity and activity overview

Login and registration remain reachable as authentication utilities. All operational modules are
member-only and redirect anonymous visitors to login. The same boundary is enforced by FastAPI;
public fleet data uses a dedicated schema that omits pending-member counts, account usernames,
applications and internal directory fields.

## Member workspace

After login, the sidebar expands to the New Captain Guide, Build Designer, guides, groups,
calendar, forum and fleet management. Personal links remain in the top navigation.

## Build catalog audit

Every active Build Designer category must contain a non-empty, unique and source-labelled option
catalog. Category-specific validation additionally enforces the minimum audited catalog sizes and
metadata contracts for lanterns, upgrades, weapons and Specialists.

The B20-facing catalog uses the current `Specialists` terminology in the interface while keeping
the legacy `special_crew` API/database key for compatibility with saved builds.

Exact game balance values can change with live updates. The application stores normalized planning
modifiers for comparison and records a catalog revision in each audited row; these values are not a
substitute for an official machine-readable game export.
