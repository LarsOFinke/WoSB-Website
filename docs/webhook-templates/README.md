# Webhook Message Templates

This directory contains versioned, copy-ready **English** message templates for every webhook event currently published by the backend.

## Usage

1. Sign in as an administrator and open **Staff Panel → Discord Webhooks**.
2. Create or edit a webhook subscription and select the required event.
3. Open the matching file under [`message-templates/`](message-templates/).
4. Copy the complete file content into **Message template**.
5. Save the subscription and send a test delivery.

The templates can be used with both delivery modes:

- **Discord Chat Webhook:** the backend renders the template and sends the final message directly to a native Discord channel webhook.
- **Signed JSON Webhook:** the template is transmitted as `destination.message_template`; the bot or integration service decides whether and how to render it.

## Links

`{resource.url}` is emitted as an absolute website URL. In production, the backend derives the public origin from the first HTTP(S) entry in `CORS_ORIGINS`. Keep the canonical website URL first, for example:

```env
CORS_ORIGINS=https://royal-blackwater-fleet.eu,https://127.0.0.1
```

For deleted builds and guides, the URL points to the corresponding collection page because the removed detail page no longer exists.

## Placeholders

Common placeholders:

- `{event}` — event type
- `{id}` — unique delivery ID
- `{occurred_at}` — event time in UTC
- `{destination.name}` — webhook subscription name
- `{actor.display_name}` and `{actor.username}` — user who triggered the event
- `{resource.type}`, `{resource.id}`, and `{resource.url}` — affected resource and website link
- `{scope.type}`, `{scope.id}`, `{scope.fleet_id}`, `{scope.squad_id}` — routing scope
- `{data.<field>}` — event-specific payload data

Missing placeholders render as empty text. Conditional sections are not supported. Discord mentions remain disabled for security reasons.

## Files

- [`all-message-templates.md`](all-message-templates.md) — every template in a single document
- [`message-templates/`](message-templates/) — one plain-text file per event
- [`signed-json-envelope.example.json`](signed-json-envelope.example.json) — sample signed JSON payload

File names match the backend event catalog exactly. The repository check fails when an event is added without a matching copy-ready template or when a linkable template omits `{resource.url}`.
