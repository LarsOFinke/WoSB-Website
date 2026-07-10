# Release 0.16.0 — Fleet squads and scoped calendar planning

## Purpose

Squads add a permanent organization layer between the official fleet and short-lived group-search
announcements. A squad is a stable sub-unit with a named leader, optional officers, a roster,
operational focus and its own calendar scope.

## Roles

- Administrators, moderators, Fleet Admirals and Fleet Lieutenants create and archive squads.
- Every squad has exactly one active command assignment in normal service operation.
- Squad Leaders manage the unit profile, member roster, officer assignments and leadership transfer.
- Squad Officers support member organization and squad calendar entries but cannot promote
  themselves, replace the leader or remove another officer.
- Squad Members can view their squad and its private calendar entries.

Squad roles are scoped to the squad and never grant global Fleet Management access.

## Calendar visibility

- Fleet-wide events are visible to every authenticated user.
- Squad events are visible to squad members, squad command and fleet/staff leadership.
- Fleet/staff leadership may create fleet-wide entries and entries for any active squad.
- Squad Leaders and Officers may create entries only for squads they manage.
- Event cancellation uses the same scope permission as event creation.

## Frontend routes

```text
/squads          active squad overview
/squads/new      fleet-command squad creation
/squads/:id      squad briefing, roster and management
/calendar        combined visible fleet/squad calendar
/calendar/new    scope-aware event creation
```

## Database migration

Migration `5d9a3b7c1e20` adds `squads`, `squad_members` and nullable
`fleet_events.squad_id`. Existing fleet events remain fleet-wide because their new scope is `NULL`.
The migration does not recreate or reseed PostgreSQL.
