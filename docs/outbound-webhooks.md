# Outbound Webhooks

The Staff Panel section **Integrations → Outbound webhooks** publishes signed application events to an external bot or integration service. It is designed for a separate Discord bot that decides which Discord channel to use and how to render the final message.

## Delivery request

Each delivery is an HTTP `POST` with a JSON body and these headers:

- `Content-Type: application/json; charset=utf-8`
- `X-RBF-Event`: event type, for example `calendar.event.created`
- `X-RBF-Delivery`: unique delivery identifier
- `X-RBF-Timestamp`: Unix timestamp used for replay protection
- `X-RBF-Signature`: `sha256=<hex digest>`

The signature is an HMAC-SHA256 digest of the **exact raw request body**, using the signing secret shown after webhook creation or secret rotation.

Python verification example:

```python
import hashlib
import hmac


def verify_webhook(raw_body: bytes, signature_header: str, secret: str) -> bool:
    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)
```

The receiving bot should also reject timestamps outside a short tolerance, such as five minutes, and store `X-RBF-Delivery` values to prevent replayed deliveries.

## Payload envelope

```json
{
  "id": "unique-delivery-id",
  "event": "calendar.event.created",
  "occurred_at": "2026-07-14T12:00:00+00:00",
  "source": "royal-blackwater-fleet",
  "destination": {
    "channel_key": "events",
    "message_template": "Optional routing or formatting hint"
  },
  "actor": {
    "id": 12,
    "username": "captain",
    "display_name": "Captain",
    "role": "moderator"
  },
  "resource": {
    "type": "calendar_event",
    "id": "42",
    "url": "/calendar"
  },
  "data": {
    "id": 42,
    "title": "Port battle"
  }
}
```

`channel_key` is intentionally not a Discord channel ID. It is a stable routing key such as `events`, `guides`, or `builds`. The external bot maps that key to the appropriate Discord server and channel.

`message_template` is passed through unchanged. The external bot may ignore it, use it as a template identifier, or interpret it as a formatting hint.

## Event catalog

The initial event catalog contains:

- `calendar.event.created`
- `calendar.event.updated`
- `calendar.event.cancelled`
- `guide.created`
- `guide.updated`
- `guide.removed`
- `newcomer_guide.updated`
- `build.created`
- `build.updated`
- `build.removed`
- `forum.thread.created`
- `forum.thread.updated`
- `integration.test`

## Delivery behavior

- New events are persisted before delivery.
- Delivery is attempted as a FastAPI background task after the API response is prepared.
- Successes and failures are visible in the Staff Panel.
- Administrators can retry failed deliveries manually.
- A test delivery can be sent from each configured webhook.
- Full signing secrets are shown only after creation or rotation.
- Production endpoints must use HTTPS.

The signing secret is stored server-side because it is required to generate HMAC signatures. Database backups and database access therefore need to be treated as sensitive.
