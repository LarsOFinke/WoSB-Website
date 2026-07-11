# Markdown content and editing

## Decision

User-authored long-form content is stored as Markdown source in the existing database text columns. Rendered HTML is not persisted.

This applies to:

- guides,
- forum opening posts,
- forum replies,
- newcomer guide text blocks.

Existing plain text remains compatible because it is valid Markdown. No database migration is required.

## Why Markdown source is stored

Keeping the authoring source in the database preserves search, ownership, permissions, attachments, linked builds and backups in one transactional data model. It also avoids coupling stored records to one HTML renderer or sanitizer version.

Pre-rendered HTML is deliberately not stored because it would:

- require trusted sanitization before every write,
- make later renderer changes and migrations harder,
- increase the risk of unsafe legacy HTML remaining in the database,
- be less pleasant to edit manually.

Files are still used for uploaded media. Content records reference them through the existing `[[file:<id>|<size>]]` tokens. Guide build cards continue to use `[[build:<id>|<layout>]]`.

## Rendering and security

The frontend uses `markdown-it` for parsing and DOMPurify for defense-in-depth sanitization before Vue receives the generated HTML.

Security choices:

- raw HTML in Markdown is disabled,
- generated HTML is sanitized before `v-html`,
- inline styles and `<style>` elements are forbidden,
- Markdown image syntax is disabled,
- images and other media must use validated uploaded-file embeds,
- generated links use `rel="noopener noreferrer"`,
- the existing backend embed validation still requires every referenced file or build to belong to the submitted content.

The custom file/build tokens are split from the Markdown text and rendered as Vue components. A token therefore acts as a content-block boundary; Markdown lists or blockquotes should not be continued across an embedded media/build card.

## Editor

`frontend/src/core/components/MarkdownEditor.vue` provides a reusable source editor with controls for:

- bold and italic text,
- headings,
- bullet and numbered lists,
- blockquotes,
- links,
- inline code and code blocks.

All affected forms retain a live preview. Attachment and build tools insert their existing tokens at the current editor position. Removing an attachment now also removes its file-embed token from the source.

## Editing permissions

### Guides

- `PUT /api/guides/{guide_id}`
- The guide owner or a moderator/admin may update it.
- Title, category, summary, body, attachments and linked builds are replaced atomically.
- The UI route is `/guides/{id}/edit`.

### Forum threads

- `PUT /api/forum/threads/{thread_id}`
- The thread owner or a moderator/admin may update it.
- Title, category, opening-post body and opening-post attachments are replaced atomically.
- The UI route is `/forum/{id}/edit`.

### Forum replies

- `PUT /api/forum/posts/{post_id}`
- The post author or a moderator/admin may update it.
- Body and attachments are replaced atomically.
- Replies are edited inline on the thread page.

Unauthorized update attempts return the same not-found response used by the existing ownership-sensitive delete behavior, avoiding unnecessary disclosure about protected resources.

## Compatibility and deployment

There is no schema migration for this feature. Deploy the backend and frontend together, then rebuild the frontend dependencies because `markdown-it` and `dompurify` were added to `frontend/package.json` and `frontend/package-lock.json`.

Typical update command:

```bash
sudo ./update.sh --migrate --seed
```

`--migrate` remains safe even though this feature itself adds no migration. Existing seed behavior and master-data overrides are unchanged.

## Validation

The implementation is covered by backend regression tests for:

- guide edits by owners,
- guide moderation edits,
- denied edits by unrelated users,
- thread metadata and opening-post edits,
- forum reply edits,
- moderator edits of forum replies,
- preservation of Markdown source.

The full backend suite, locale completeness check and Vite production build should be run before deployment.
