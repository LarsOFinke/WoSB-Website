# Raid-Helper calendar integration

The calendar can create, update and cancel Raid-Helper events through the official v4 API. The integration is intentionally split into normalized profiles, destinations, templates and per-event synchronization links.

## Administration

Only administrators can access **Staff Panel → Raid-Helper**.

A **profile** stores one Discord server ID, an encrypted API key, the API base URL, authorization-header mode and the server timezone. API keys use the same authenticated encryption and rotation mechanism as Discord webhook credentials and are never returned to the frontend.

A **destination** binds one profile and Discord channel to exactly one calendar scope:

- fleet-wide calendar, or
- one specific squad calendar.

Destinations may be restricted to selected calendar categories. An empty category list accepts all categories. Default destinations are preselected when an event is created.

A **template** belongs to one profile and can be limited to fleet events, squad events or both. Category restrictions work in the same way as destinations. The Staff page includes versioned fleet and squad presets based on the existing calendar webhook messages.

## Event workflow

The event form enables Raid-Helper delivery by default. When the scope or category changes, the frontend requests only compatible destinations and templates. The user may disable delivery or select several destinations, including destinations from different profiles.

Local calendar persistence is transactional with the selected synchronization links. A temporary Raid-Helper outage does not discard the local event: each external link records queued, delivered or failed state for event managers. Updates and cancellations use the stored external event/message ID.

## Template context

Title, description, announcement and JSON payload fields use the existing safe placeholder renderer. Useful values include:

- `{{event.title}}`, `{{event.category}}`, `{{event.description}}`, `{{event.location}}`
- `{{event.start_at}}`, `{{event.end_at}}`, `{{event.date}}`, `{{event.time}}`
- `{{event.start_unix}}`, `{{event.end_unix}}`, `{{event.duration_minutes}}`
- `{{event.timezone}}`
- `{{scope.type}}`, `{{scope.name}}`, `{{scope.squad_id}}`
- `{{raid_helper.template_id}}`
- `{{rendered.title}}`, `{{rendered.description}}`, `{{rendered.announcement}}`

The JSON payload is administrator-managed because Raid-Helper template fields can evolve independently from this project. The API base is restricted to official HTTPS Raid-Helper hosts and must end in `/api/v4`.

## Deployment

Migration `0014_raid_helper_calendar` creates the integration tables and adds the event-level delivery toggle. No seed is required.
