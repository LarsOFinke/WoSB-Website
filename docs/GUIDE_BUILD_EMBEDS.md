# Guide Build Embeds

Guides can now use Builds as first-class references.

## Authoring UX

The Guide creation form includes a dedicated Build tools panel:

- choose an existing Build from the dropdown,
- link it as a general Guide reference, or
- insert it inline at the current cursor position.

The inline token is intentionally simple:

```text
[[build:12|card]]
```

Supported layouts:

```text
compact
card
full
```

`card` is the default layout and is suitable for most Guide text. `compact` is useful in dense checklist paragraphs. `full` gives the Build card the full content width.

## Backend model

General Guide-to-Build references live in `guide_build_references`:

```text
guide_id
build_id
sort_order
```

The table is a join table, so Build metadata is not copied into Guides. Guide responses expose linked Builds through the existing `BuildRead` schema.

## Validation rules

The backend validates inline Build markers during Guide creation:

- every `[[build:id|layout]]` must reference a Build that exists,
- every inline Build must also be present in `build_ids`,
- layout must be one of `compact`, `card`, `full`,
- inline Build embeds are capped to keep rendering predictable.

This mirrors the existing file embed model: content placement is stored in text, but the allowed references are stored as explicit relations.

## Future upgrade path

The current token format keeps the prototype KISS-friendly. A later rich-text editor can store structured blocks while still migrating from these markers because the relation table already contains the canonical Build references.
