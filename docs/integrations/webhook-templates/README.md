# English Discord message templates

[`all-message-templates.md`](all-message-templates.md) is the single copy-ready
English message-template reference for native Discord channel webhooks. Paste
the complete code block for an event into the **Message template** field in
**Staff Panel → Discord Webhooks**.

The language-neutral event catalog is the only maintained source. The Staff
Panel template autofill, backend event defaults, and this grouped reference are
derived from it. There are deliberately no per-event `.txt` files anymore.

The templates are intended only for direct Discord delivery by this backend. They use Discord Markdown and event payload placeholders. Useful common placeholders include:

- `{event}`
- `{occurred_at}`
- `{actor.display_name}`
- `{resource.id}`
- `{resource.url}`
- event-specific values under `{data...}`

The catalog is grouped by event area so operational, moderation, content, and
community notifications can be found without scanning one unstructured list.

Repository checks ensure that each supported event has exactly one catalog
entry, every placeholder exists in that event's preview payload, and rendered
messages stay within Discord's content limit.
