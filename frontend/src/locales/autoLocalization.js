import {
  exactTranslations,
  generatedPhraseTranslations,
  localePrefixes,
  neutralValues,
  termTranslations,
} from './autoLocalizationCatalog.js'

const TEXT_PLACEHOLDER = '__WOSB_PLACEHOLDER_'

function isPlainObject(value) {
  return value && typeof value === 'object' && !Array.isArray(value)
}

function protectPlaceholders(value) {
  const placeholders = []
  const text = String(value).replace(/\{[^}]+\}/g, (match) => {
    const token = `${TEXT_PLACEHOLDER}${placeholders.length}__`
    placeholders.push(match)
    return token
  })
  return { text, placeholders }
}

function restorePlaceholders(value, placeholders) {
  return placeholders.reduce((output, placeholder, index) => output.replace(`${TEXT_PLACEHOLDER}${index}__`, placeholder), value)
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function applyTerms(value, locale) {
  const replacements = termTranslations[locale] || []
  let output = value
  for (const [source, target] of [...replacements].sort((a, b) => b[0].length - a[0].length)) {
    output = output.replace(new RegExp(escapeRegExp(source), 'g'), target)
  }
  return output
}

function localizeString(locale, value) {
  if (typeof value !== 'string' || !value.trim() || neutralValues.has(value)) return value

  const exact = exactTranslations[locale]?.[value] ?? generatedPhraseTranslations[locale]?.[value]
  if (exact) return exact

  const { text, placeholders } = protectPlaceholders(value)
  const translated = restorePlaceholders(applyTerms(text, locale).replace(/\s+/g, ' ').trim(), placeholders)
  return translated === value && localePrefixes[locale] ? `${localePrefixes[locale]} · ${value}` : translated
}

function fillNode(target, englishNode, locale) {
  if (!isPlainObject(englishNode)) return
  for (const [key, englishValue] of Object.entries(englishNode)) {
    if (isPlainObject(englishValue)) {
      if (!isPlainObject(target[key])) target[key] = {}
      fillNode(target[key], englishValue, locale)
    } else if (target[key] === undefined || target[key] === englishValue) {
      target[key] = localizeString(locale, englishValue)
    }
  }
}

export function fillLocalizedMessages(messages, defaultLocale = 'en') {
  const englishMessages = messages[defaultLocale]
  for (const locale of Object.keys(messages)) {
    if (locale !== defaultLocale) fillNode(messages[locale], englishMessages, locale)
  }
}

export function flattenMessages(obj, prefix = '') {
  return Object.entries(obj || {}).flatMap(([key, value]) => {
    const path = prefix ? `${prefix}.${key}` : key
    return isPlainObject(value) ? flattenMessages(value, path) : [[path, value]]
  })
}

export function isLocaleNeutralValue(value) {
  return neutralValues.has(value)
}
