# Raid-Helper calendar integration

The calendar can create, update and cancel Raid-Helper events through the official v4 API. The integration is intentionally split into normalized profiles, destinations, templates and per-event synchronization links.

## Administration

Only administrators can access **Staff Panel → Raid-Helper**.

A **profile** stores one Discord server ID, an encrypted API key, the API base URL, server timezone and an optional default Discord leader user ID. API keys use the same authenticated encryption and rotation mechanism as Discord webhook credentials and are never returned to the frontend.

A **destination** binds one profile and Discord channel to exactly one calendar scope:

- fleet-wide calendar, or
- one specific squad calendar.

Destinations may be restricted to selected calendar categories. An empty category list accepts all categories. Default destinations are preselected when an event is created.

A **template** belongs to one profile and can be limited to fleet events, squad events or both. Category restrictions work in the same way as destinations. The Staff page includes versioned fleet and squad presets based on the existing calendar webhook messages.

Templates default to **free-compatible mode**. In that mode the outgoing JSON is limited to `title`, `description`, `date`, `time` and `duration`; the application injects the validated `leaderId`. Custom Raid-Helper template IDs and additional top-level kwargs require the explicit **Raid-Helper Premium features** toggle. The backend enforces this distinction when templates are saved and again immediately before delivery, so an invalid free-mode template never reaches Raid-Helper.

The profile test checks server event-list read access only and reports that limited scope explicitly. Each destination also has an opt-in write test that creates and immediately deletes a temporary event in the configured channel. Staff select the exact application template to test, so the probe exercises the same saved API key, server ID, channel ID, leader ID, rendered JSON payload, optional `templateId`, create endpoint and delete endpoint as calendar synchronization. A separate minimal-payload option remains available for isolating base destination authorization.

## Event workflow

The event form enables Raid-Helper delivery by default. When the scope or category changes, the frontend requests only compatible destinations and templates. The user may disable delivery or select several destinations, including destinations from different profiles. Each selected destination uses its current profile default leader ID unless the event manager chooses a manual Discord user ID for that appointment. Manual overrides are stored on the synchronization link; profiles without a default automatically require a manual leader.

Local calendar persistence is transactional with the selected synchronization links. A temporary Raid-Helper outage does not discard the local event: each external link records queued, delivered or failed state for event managers. Updates and cancellations use the stored external event/message ID.

## Template context

Title, description, announcement and JSON payload fields use the existing safe placeholder renderer. Useful values include:

- `{{event.title}}`, `{{event.category}}`, `{{event.description}}`, `{{event.location}}`
- `{{event.start_at}}`, `{{event.end_at}}`, `{{event.date}}`, `{{event.time}}`
- `{{event.start_unix}}`, `{{event.end_unix}}`, `{{event.duration_minutes}}`
- `{{event.timezone}}`
- `{{scope.type}}`, `{{scope.name}}`, `{{scope.squad_id}}`
- `{{raid_helper.template_id}}`, `{{raid_helper.leader_id}}` (JSON payload templates)
- `{{rendered.title}}`, `{{rendered.description}}`, `{{rendered.announcement}}`

The Raid-Helper template ID is optional and treated as a Premium capability. Leave it blank to use the server default template. Enter an exact custom template ID only after enabling Premium features for the application template and only when the Discord server has Raid-Helper Premium. The application omits an empty ID and the legacy `Standard` sentinel instead of sending an explicit `templateId`.

The free-compatible payload preset intentionally mirrors the proven basic API call: `title`, `description`, `date`, `time` and `duration`. The Premium preset adds the optional template ID, announcement and advanced kwargs. Administrators may edit the JSON, but additional top-level keys are rejected while Premium features are disabled. The application always injects the validated effective leader as the top-level `leaderId`, so templates cannot accidentally omit or replace the required value. Calendar dates are rendered in Raid-Helper's `DD.MM.YYYY` format after conversion to the profile timezone. The API base is restricted to official HTTPS Raid-Helper hosts and must end in `/api/v4`. Requests authenticate with the API key as the raw `Authorization` header value; accidental surrounding quotes, whitespace and a pasted `Bearer ` wrapper are normalized before transmission, while `X-API-Key` remains unsupported.

## Deployment

Migration `0014_raid_helper_calendar` creates the integration tables and adds the event-level delivery toggle. Migration `0016_raid_helper_api_host` canonicalizes the v4 host and safe defaults. Migration `0017_raid_helper_leaders` adds the optional profile default and per-event leader override. Migration `0018_raid_helper_raw_auth` removes the obsolete configurable authorization mode so every saved profile uses Raid-Helper's required raw `Authorization` header. Migration `0019_raid_helper_template_id` clears the application-generated `Standard` sentinel and makes the database default an empty optional template ID. Migration `0020_raid_helper_premium` adds the explicit Premium-capability flag, converts the former application-recommended default payload to the free-compatible preset, and marks preserved custom/advanced templates as Premium. No seed is required.
