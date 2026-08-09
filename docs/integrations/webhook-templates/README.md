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
- `{actor.display_name}` and `{actor.username}`
- `{resource.id}`
- `{resource.type}`
- `{data.summary}`

The catalog is grouped by event area so operational, moderation, content, and
community notifications can be found without scanning one unstructured list.

Repository checks ensure that each supported event has one distinct catalog
entry, every placeholder is supported by the Spring renderer, and rendered
messages stay within Discord's content limit.
