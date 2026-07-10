# Release 0.16.2 — My Squads workspace

## Goal

Separate the fleet-wide squad directory from the personal daily workspace. `/squads` remains the
organizational overview, while `/profile/squads` answers three personal questions immediately:

1. Which active squads am I explicitly assigned to?
2. Which of those units may I organize?
3. What squad appointments are coming up next?

## Access and privacy

`GET /api/squads/mine` requires an authenticated session and returns only active squad assignments
linked to the user's active fleet membership. Administrator, moderator or fleet-leadership status
alone does not add a squad to this result. Squad calendar visibility continues to be enforced by the
existing server-side calendar policy.

## User experience

The personal top bar and profile tools now include **My Squads**. The page separates command units
from ordinary memberships, shows the user's actual squad role, member capacity and next appointment,
and provides direct actions for the squad detail, filtered calendar and event creation when allowed.
The fleet-wide squad directory links back to the personal workspace and displays the user's actual
role instead of a generic membership badge.

## Deployment

This release changes API serialization and frontend routes only. It requires neither an Alembic
migration nor a seed run. Deploy with the default database-safe update path:

```bash
sudo ./update.sh
```
