# Inline media embeds

Guides and forum posts support attachment placement directly inside the text body. The editor stores placement as a small, explicit marker instead of introducing a rich-text dependency:

```text
[[file:123|large]]
```

## Supported sizes

- `small`
- `medium`
- `large`
- `full`

The frontend editor inserts these markers through the attachment tools, so most users do not need to type them manually. The renderer resolves the file id against the attachments of the same guide/post and displays images, videos, PDFs and text files inline. Files that are uploaded but not referenced in the body remain visible as normal attachments below the content.

## Validation

The backend keeps the prototype lightweight but protects the most important operational limits:

- uploaded files must use one of the allowed MIME types and extensions
- empty files are rejected
- max upload size is capped by type:
  - images: 12 MB
  - documents/text: 20 MB
  - videos: 80 MB
- forum posts accept up to 12 attached files
- guides accept up to 20 attached files
- inline markers may only reference files attached to the same guide/post
- inline marker sizes must be one of the supported size tokens above

This keeps the implementation easy to replace with a real rich-text editor later while preserving clean backend guarantees now.
