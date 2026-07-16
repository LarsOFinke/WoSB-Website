# English Discord message templates

Every file in [`message-templates/`](message-templates/) contains one copy-ready English message template for a native Discord channel webhook. Paste the complete file content into the **Message template** field in **Staff Panel → Discord Webhooks**.

The templates are intended only for direct Discord delivery by this backend. They use Discord Markdown and event payload placeholders. Useful common placeholders include:

- `{event}`
- `{occurred_at}`
- `{actor.display_name}`
- `{resource.id}`
- `{resource.url}`
- event-specific values under `{data...}`

[`all-message-templates.md`](all-message-templates.md) provides a single catalog for browsing. The individual `.txt` files remain the easiest copy source.

Repository checks ensure that each supported event has exactly one template, every placeholder exists in that event's preview payload and rendered messages stay within Discord's content limit.
