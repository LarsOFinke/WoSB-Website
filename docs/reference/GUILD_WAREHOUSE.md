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
whole-number amount, whole-row reservation flag, and collection status. `up_for_collection`
means the donation is waiting at the port; `in_warehouse` means it has reached the fleet
warehouse. Its holder is exactly one of:

- an active member of the selected fleet, linked by user ID; or
- a custom operational name for an external player or unregistered holder.

Linked entries resolve the member's current display name when read. A custom name is
stored as entered after whitespace normalization. Ports come from the dedicated,
administrator-maintained `warehouse_ports` reference catalog; warehouse writes reject
names that are not currently active. Resources remain normalized free text in this
prototype. Amounts are limited to `999,999,999`.

The `version` field implements optimistic concurrency. Every successful update advances
it. Update and delete clients must send the version they read; stale mutations return
`409 Conflict` and must reload before retrying. The immutable Flyway migration is
`V12__guild_warehouse.sql`; `V13__warehouse_port_catalog.sql` adds the managed game-port
catalog and its initial World of Sea Battle values. `V14__warehouse_collection_and_pickup_assignments.sql`
adds collection state and the fleet/port pickup-assignee relation.

Each active fleet port may have one optional pickup assignee. The assignee must be an
active member of that fleet; assignment changes are staff-only and are audited. Entries
show the current assignment for their fleet and port, so donations remain stacked by
fleet while collection work can be distributed.

## Member API and staff editing

All endpoints require authentication and the normal host/origin boundary. Reading is
available to every authenticated member. Mutations additionally require a moderator or
administrator and CSRF protection:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/warehouse` | Member-visible bounded rows, aggregate totals, and filter facets |
| `GET` | `/api/warehouse/ports` | Active game-port choices for authenticated members |
| `GET` | `/api/warehouse/port-assignments?fleet_id=...` | Fleet port pickup assignees (members may read their fleet) |
| `PUT` | `/api/warehouse/port-assignments/{port_id}` | Staff assigns or clears a fleet-port pickup member |
| `POST` | `/api/warehouse` | Staff-only entry creation |
| `PUT` | `/api/warehouse/{entry_id}` | Staff-only replacement using its version |
| `DELETE` | `/api/warehouse/{entry_id}?version=...` | Staff-only deletion using its version |

The list accepts `fleet_id`, exact case-insensitive `holder`, `port`, `resource`,
`reserved`, `collection_status`, `limit`, and `offset`. Totals describe the complete matching result, not
only the returned page: matching stock, reserved stock, available stock, and row count.
Facet values are scoped to the selected fleet so the UI can reproduce the spreadsheet
prototype's dropdown workflow.

The route `/warehouse` appears in member navigation. Every authenticated member can
browse, filter, and review aggregate totals and reservation state. Create, edit, and
delete controls render only for moderators and administrators; the backend enforces the
same boundary independently. Staff member selection reuses the fleet-management view
instead of exposing general user-administration data.

Administrators manage ports through the **Warehouse ports** tab in
`/admin/master-data`. The corresponding `/api/admin/master-data/warehouse-ports`
collection supports listing, creation, updates, and deactivation. Deactivated ports
disappear from warehouse dropdowns and cannot be submitted on new mutations, while
historical stock rows remain readable. Renaming a catalog port updates matching stock
rows and advances their optimistic versions so open editors fail safely instead of
overwriting the rename.

## Audit and Discord delivery

Create, material update, reservation-only update, and delete actions write a bounded
audit record in the warehouse database transaction. After commit, the existing async
webhook listener maps them to:

- `warehouse.stock.changed` for creates, stock/detail changes, and deletes;
- `warehouse.reservation.changed` when only reservation state changes.
- `warehouse.stock.overview` after either event, containing the current fleet totals
  and every port/resource line for a member-facing full overview.

Events carry fleet scope, so administrators can subscribe different Discord targets by
fleet and event type through the existing webhook administration. Delivery failures do
not roll back inventory changes. The overview contains fleet name, total/available/
reserved amounts, and port/resource totals. Messages contain only operational warehouse
data and actor display name; they contain no webhook secret,
session credential, private member note, or complete IP address. Discord webhook URLs
remain encrypted server-side and never enter the frontend bundle.

## Privacy and lifecycle

A linked member ID is personal data used to associate inventory with the correct fleet
member. It is included in that account's personal-data export through the warehouse
relation. Account deletion follows the existing pseudonymization workflow; the entry
remains operational while its linked identity resolves to the pseudonymized account.
Staff delete entries when stock is no longer operationally relevant.

Custom holder names are operational aliases without a reliable account relation. If an
alias identifies a person, correction, export, or deletion requires a staff member to
locate it by name and handle it manually. Avoid real-world names or contact details when
an in-game name is sufficient.

## Future spreadsheet client

The supplied spreadsheet remains a UI prototype, not a synchronized datastore. A future
Apps Script client should call this API and must not duplicate validation or send Discord
webhooks directly. The browser endpoints currently use session-cookie and CSRF security;
an unattended sheet therefore needs a separately designed, revocable, narrowly scoped
machine credential before integration. Do not embed administrator cookies, Discord URLs,
or long-lived general API secrets in a shared sheet.
