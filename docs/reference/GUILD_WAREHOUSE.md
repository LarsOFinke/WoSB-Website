# Guild Warehouse

The Guild Warehouse is the authoritative inventory for fleet logistics. PostgreSQL
stores the state, the Spring service owns validation and audit behavior, and the Vue
workspace is the first administration client. Discord receives notifications through
the existing website-webhook pipeline; it is never a database or command channel.

```text
Website admin ──┐
                ├──> Warehouse API -> service -> PostgreSQL
Future sheet ───┘                         |
                                          +-> audit event -> Discord webhook
```

## Data model

Each entry belongs to one active fleet and contains a port, resource, non-negative
whole-number amount, and whole-row reservation flag. Its holder is exactly one of:

- an active member of the selected fleet, linked by user ID; or
- a custom operational name for an external player or unregistered holder.

Linked entries resolve the member's current display name when read. A custom name is
stored as entered after whitespace normalization. Port and resource are deliberately
validated free text in this prototype so the workflow does not depend on a new master
data catalog. Amounts are limited to `999,999,999`.

The `version` field implements optimistic concurrency. Every successful update advances
it. Update and delete clients must send the version they read; stale mutations return
`409 Conflict` and must reload before retrying. The immutable Flyway migration is
`V12__guild_warehouse.sql`.

## Administrator API and UI

All endpoints require an authenticated administrator, CSRF protection for mutations,
and the normal host/origin boundary:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/admin/warehouse` | Bounded rows, aggregate totals, and filter facets |
| `POST` | `/api/admin/warehouse` | Create an entry |
| `PUT` | `/api/admin/warehouse/{entry_id}` | Replace an entry using its version |
| `DELETE` | `/api/admin/warehouse/{entry_id}?version=...` | Delete using its version |

The list accepts `fleet_id`, exact case-insensitive `holder`, `port`, `resource`,
`reserved`, `limit`, and `offset`. Totals describe the complete matching result, not
only the returned page: matching stock, reserved stock, available stock, and row count.
Facet values are scoped to the selected fleet so the UI can reproduce the spreadsheet
prototype's dropdown workflow.

The route `/admin/warehouse` sits in the shared Staff shell but is visible only to
administrators. It supports linked-member and custom-name entry, editing, deletion,
reservation state, responsive table presentation, and the same summary cards as the
prototype.

## Audit and Discord delivery

Create, material update, reservation-only update, and delete actions write a bounded
audit record in the warehouse database transaction. After commit, the existing async
webhook listener maps them to:

- `warehouse.stock.changed` for creates, stock/detail changes, and deletes;
- `warehouse.reservation.changed` when only reservation state changes.

Events carry fleet scope, so administrators can subscribe different Discord targets by
fleet and event type through the existing webhook administration. Delivery failures do
not roll back inventory changes. Messages contain only the operational holder, port,
resource, amount transition, and actor display name; they contain no webhook secret,
session credential, private member note, or complete IP address. Discord webhook URLs
remain encrypted server-side and never enter the frontend bundle.

## Privacy and lifecycle

A linked member ID is personal data used to associate inventory with the correct fleet
member. It is included in that account's personal-data export through the warehouse
relation. Account deletion follows the existing pseudonymization workflow; the entry
remains operational while its linked identity resolves to the pseudonymized account.
Administrators delete entries when stock is no longer operationally relevant.

Custom holder names are operational aliases without a reliable account relation. If an
alias identifies a person, correction, export, or deletion requires an administrator to
locate it by name and handle it manually. Avoid real-world names or contact details when
an in-game name is sufficient.

## Future spreadsheet client

The supplied spreadsheet remains a UI prototype, not a synchronized datastore. A future
Apps Script client should call this API and must not duplicate validation or send Discord
webhooks directly. The browser endpoints currently use session-cookie and CSRF security;
an unattended sheet therefore needs a separately designed, revocable, narrowly scoped
machine credential before integration. Do not embed administrator cookies, Discord URLs,
or long-lived general API secrets in a shared sheet.
