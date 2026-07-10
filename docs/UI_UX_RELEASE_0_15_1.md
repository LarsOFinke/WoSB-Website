# UI/UX Release 0.15.1

## Fleet-management visibility and access

The Fleet Management module is now visible only to:

- site administrators,
- site moderators,
- active Fleet Admirals,
- active Fleet Lieutenants.

Regular members no longer see the sidebar entry. Direct navigation to `/fleets` is redirected to the profile page, and management API endpoints return HTTP 403 without an eligible site or fleet role.
