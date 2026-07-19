const OFFICIAL_DISCORD_WEBHOOK_URL = /^https:\/\/(?:discord\.com|www\.discord\.com|ptb\.discord\.com|canary\.discord\.com|discordapp\.com)\/api(?:\/v\d{1,2})?\/webhooks\/[^/\s]+\/[^/\s]+(?:\/(?:github|slack))?\/?(?:\?[^#\s]*)?$/i

export function normalizeDiscordWebhookUrl(value) {
  const trimmed = String(value || '').trim()
  if (trimmed.startsWith('<') && trimmed.endsWith('>')) return trimmed.slice(1, -1).trim()
  return trimmed
}

export function webhookDraftIssues(form, { editing = false } = {}) {
  const issues = []
  const name = String(form.name || '').trim()
  const endpointUrl = normalizeDiscordWebhookUrl(form.endpoint_url)
  const scopeId = Number(form.scope_id)

  if (name.length < 3) issues.push('name')
  if (!editing && !endpointUrl) issues.push('endpointRequired')
  if (endpointUrl && !OFFICIAL_DISCORD_WEBHOOK_URL.test(endpointUrl)) issues.push('endpointInvalid')
  if (form.scope_type !== 'global' && (!Number.isInteger(scopeId) || scopeId < 1)) issues.push('scope')
  if ((form.event_types || []).length === 0 && !form.broadcast_enabled) issues.push('events')
  return issues
}

export function outboundWebhookPayload(form) {
  const endpointUrl = normalizeDiscordWebhookUrl(form.endpoint_url)
  return {
    name: String(form.name || '').trim(),
    endpoint_url: endpointUrl || null,
    scope_type: form.scope_type,
    scope_id: form.scope_type === 'global' ? null : Number(form.scope_id),
    message_template: String(form.message_template || '').trim() || null,
    discord_username: String(form.discord_username || '').trim() || null,
    discord_avatar_url: String(form.discord_avatar_url || '').trim() || null,
    broadcast_enabled: Boolean(form.broadcast_enabled),
    is_active: Boolean(form.is_active),
    event_types: [...new Set(form.event_types || [])].sort(),
  }
}

