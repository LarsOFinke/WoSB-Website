# Discord channel webhooks

The Staff Panel exposes native Discord channel webhooks under **Discord Webhooks**. The website backend renders application events and posts the finished messages directly to official Discord channel webhook URLs. No Discord bot or second repository is involved.

## Setup

1. Create a webhook in Discord under **Server Settings → Integrations → Webhooks**.
2. Copy the secret URL from Discord.
3. Open **Staff Panel → Discord Webhooks**.
4. Select events, scope and an optional message template.
5. Save and use **Send test**.

Only official HTTPS URLs below Discord's `/api/webhooks/` path are accepted. The secret token is masked after saving and never returned to the browser again. Leave the URL field empty when editing to retain the current token.

## Multi-channel event routing

Webhook subscriptions are independent. The same event may be selected on any number of webhook records, so one event can be delivered to several Discord channels at the same time. Each channel receives its own persisted delivery record and can use its own:

- Discord webhook URL,
- event selection,
- global, fleet or squad scope,
- optional sender name,
- the fixed Royal Blackwater Fleet avatar,
- message template,
- active state.

There is intentionally no uniqueness constraint on event and scope combinations.

## Recommended channel profiles

The editor provides three presets. They select events only; the destination URL and final
channel choice always remain an administrator decision:

- **Moderation inbox:** new registrations, fleet applications and new data-subject requests
  that need a timely response.
- **Operations audit:** controlled update, backup, restore, backup-configuration and resolved
  privacy workflow events useful for diagnosing operational problems.
- **Calendar shoutouts:** created, changed and cancelled calendar events, phrased for public
  community channels rather than as an internal audit message.

These notifications complement the database audit history. They do not report logins, page
views, user activity or message contents and must not be used for member monitoring. Privacy
request details, resolution notes, backup credentials and restore approval secrets never enter
Discord payloads.

## Broadcast workspace

External fleet communication is managed separately under **Staff Panel → Discord Broadcasts**. Administrators maintain broadcast-only destinations for partner fleets, diplomacy channels and cross-server coordination, then send one manual Discord Markdown message to several selected channels. Automatic website-event subscriptions remain under **Discord Webhooks**.

Existing combined records remain compatible, but newly created broadcast destinations do not subscribe to automatic website events.

The panel supports:

- selecting one, several or all broadcast targets,
- one message of up to 2,000 characters,
- an optional sender-name override,
- the fixed Royal Blackwater Fleet avatar,
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

The delivery monitor is collapsed by default, so tests and refreshes do not shift the page. It records status, attempts, response code and a bounded response or error message. Failed automatic and broadcast deliveries can be retried manually. Administrators can delete an individual delivery or permanently clear the currently filtered history; webhook configurations are not changed by history cleanup.

## Message templates

Copy-ready English templates live in:

```text
docs/webhook-templates/message-templates/
```

Templates support Discord Markdown and event-specific placeholders such as `{data.build_name}` or `{resource.url}`. The repository check validates that every automatic event has a template and that all referenced placeholders exist in the event preview payload.

Broadcast messages are written directly in the Broadcast panel and do not use event templates.

Run `python3 infrastructure/scripts/generation/sync_webhook_templates.py` after changing runtime defaults; the repository
check enforces an exact match between the event catalog, preview payloads and documentation.

## Webhook avatar

Every automatic event and manual broadcast uses the bundled Royal Blackwater Fleet icon:

```text
https://royal-blackwater-fleet.eu/rbf-fleet-icon.png
```

The delivery backend sets this URL for every Discord request. The obsolete
`discord_avatar_url` API and database fields were removed; callers cannot override the fleet icon.

The gateway image normalizes all built frontend directories to mode `0755` and files to `0644`, preventing unreadable static assets from producing HTTP 403 responses.

## Credential encryption and key rotation

Discord webhook URLs contain write-capable tokens. They are stored as authenticated, versioned
Fernet ciphertext and are never returned to the browser. Setup generates
`WEBHOOK_ENCRYPTION_KEYS` in `infrastructure/.env`; this value must be backed up separately from the
database and protected with mode `0600`.

To rotate the key, prepend a newly generated key while retaining the old values temporarily:

```bash
new_key="$(openssl rand -base64 32 | tr '+/' '-_' | tr -d '\n')"
# WEBHOOK_ENCRYPTION_KEYS=new_key,current_key,older_key
```

Restart the API. The startup maintenance pass re-encrypts stored webhook credentials with the first
key. After every webhook can be tested successfully and a database backup has been taken, remove
retired keys from the environment. Never remove an old key before the rotation pass has completed.

## Forum and fleet events

Automatic website webhooks include forum replies and removals as well as fleet creation, applications, profile changes, membership updates, leadership assignments and role changes. Every supported event has a versioned English template under `docs/webhook-templates/message-templates/`. Forum reply deletion is available to the reply author and Staff after explicit confirmation; the opening post remains tied to thread deletion.

## Group-search events

The group-search module publishes automatic events for:

- `group.created` when a listing is created,
- `group.member.joined` when a captain joins,
- `group.closed` when the owner or Staff closes a listing.

Payloads intentionally omit free-text contact notes, descriptions and member
notes. Fleet-scoped routing follows the listing owner's fleet for the entire
lifecycle, not the fleet of a joining member or moderating Staff user.
