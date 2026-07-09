export function cloneMessages(source) {
  return JSON.parse(JSON.stringify(source))
}

export function mergeMessages(target, source) {
  for (const [key, value] of Object.entries(source || {})) {
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      target[key] = mergeMessages(target[key] || {}, value)
    } else {
      target[key] = value
    }
  }

  return target
}

export function getNestedValue(source, path) {
  return path.split('.').reduce((current, key) => current?.[key], source)
}

export function formatMessage(template, params = {}) {
  return String(template).replace(/\{(\w+)\}/g, (_, key) => String(params[key] ?? `{${key}}`))
}
