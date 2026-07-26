import DOMPurify from 'dompurify'
import MarkdownIt from 'markdown-it'

const markdown = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  typographer: false,
})

// Uploaded media is embedded through the application's validated [[file:...]]
// tokens. Disable remote Markdown images to avoid unreviewed tracking pixels.
markdown.disable('image')

const defaultLinkOpen = markdown.renderer.rules.link_open
  || ((tokens, index, options, _env, self) => self.renderToken(tokens, index, options))

markdown.renderer.rules.link_open = (tokens, index, options, env, self) => {
  const token = tokens[index]
  token.attrSet('target', '_blank')
  token.attrSet('rel', 'noopener noreferrer')
  return defaultLinkOpen(tokens, index, options, env, self)
}

export function renderMarkdown(source = '', options = {}) {
  const environment = {}
  const tokens = markdown.parse(String(source || ''), environment)
  if (options.headingIdPrefix) {
    let headingIndex = Number(options.headingStartIndex || 0)
    for (const token of tokens) {
      if (token.type !== 'heading_open') continue
      headingIndex += 1
      token.attrSet('id', `${options.headingIdPrefix}-${headingIndex}`)
    }
  }
  const rendered = markdown.renderer.render(tokens, markdown.options, environment)
  return DOMPurify.sanitize(rendered, {
    USE_PROFILES: { html: true },
    FORBID_TAGS: ['style'],
    FORBID_ATTR: ['style'],
  })
}
