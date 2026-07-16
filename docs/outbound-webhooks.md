# Discord channel webhooks

The Staff Panel exposes native Discord channel webhooks under **Discord Webhooks**. The website backend renders application events and posts the finished messages directly to official Discord channel webhook URLs. No Discord bot or second repository is involved.

## Setup

1. Create a webhook in Discord under **Server Settings → Integrations → Webhooks**.
2. Copy the secret URL from Discord.
3. Open **Staff Panel → Discord Webhooks**.
4. Select events, scope and an optional message template.
5. Optionally enable **Available for manual broadcasts**.
6. Save and use **Send test**.

Only official HTTPS URLs below Discord's `/api/webhooks/` path are accepted. The secret token is masked after saving and never returned to the browser again. Leave the URL field empty when editing to retain the current token.

## Multi-channel event routing

Webhook subscriptions are independent. The same event may be selected on any number of webhook records, so one event can be delivered to several Discord channels at the same time. Each channel receives its own persisted delivery record and can use its own:

- Discord webhook URL,
- event selection,
- global, fleet or squad scope,
- sender name and avatar,
- message template,
- active state.

There is intentionally no uniqueness constraint on event and scope combinations.

## Broadcast panel

Administrators can send a manual Discord Markdown message to several channels from the **Broadcast panel**.

A webhook appears as a broadcast target when it is active and **Available for manual broadcasts** is enabled. Broadcast-only webhook records are supported: they may have no automatic events selected.

The panel supports:

- selecting one, several or all broadcast targets,
- one message of up to 2,000 characters,
- optional sender-name and avatar overrides,
- safe Discord delivery with automatic mentions disabled,
- one stored delivery per target,
- the normal delivery history and retry workflow.

Broadcasts are queued and sent as background deliveries after the API response. A failure in one channel does not prevent the other selected channels from being attempted.

## Scopes

Scopes apply to automatic event subscriptions:

- **Global:** receives every matching event.
- **Fleet:** receives matching events carrying the selected fleet ID.
- **Squad:** receives matching events carrying the selected squad ID.

Manual broadcasts use the explicitly selected targets and therefore do not apply event scopes.

The delivery history records status, attempts, response code and a bounded response or error message. Failed automatic and broadcast deliveries can be retried manually.

## Message templates

Copy-ready English templates live in:

```text
docs/webhook-templates/message-templates/
```

Templates support Discord Markdown and event-specific placeholders such as `{data.build_name}` or `{resource.url}`. The repository check validates that every automatic event has a template and that all referenced placeholders exist in the event preview payload.

Broadcast messages are written directly in the Broadcast panel and do not use event templates.

## Avatar URLs

`Discord avatar URL` must be a public HTTPS image URL that Discord can fetch without authentication. The bundled fleet icon is available at:

```text
https://royal-blackwater-fleet.eu/rbf-fleet-icon.png
```

The gateway image normalizes all built frontend directories to mode `0755` and files to `0644`, preventing unreadable static assets from producing HTTP 403 responses.
