import { computed, reactive, readonly } from 'vue'

import { DEFAULT_LOCALE, SUPPORTED_LOCALES } from './config'
import { optionTermGlossaries } from './glossaries/optionTerms'
import { messages } from './messages'
import { formatMessage, getNestedValue } from './utils'

export { DEFAULT_LOCALE, SUPPORTED_LOCALES }

const LOCALE_STORAGE_KEY = 'rbv-hub.locale'
const LEGACY_LOCALE_STORAGE_KEY = 'blackwater-hub.locale'

function normalizeLocale(locale) {
  return SUPPORTED_LOCALES.some((entry) => entry.code === locale) ? locale : DEFAULT_LOCALE
}

function getHtmlLang(locale) {
  return SUPPORTED_LOCALES.find((entry) => entry.code === locale)?.htmlLang || 'en'
}

function readStoredLocale() {
  if (typeof localStorage === 'undefined') return DEFAULT_LOCALE
  const stored = localStorage.getItem(LOCALE_STORAGE_KEY) || localStorage.getItem(LEGACY_LOCALE_STORAGE_KEY)
  if (stored && !localStorage.getItem(LOCALE_STORAGE_KEY)) localStorage.setItem(LOCALE_STORAGE_KEY, stored)
  return stored || DEFAULT_LOCALE
}

function persistLocale(locale) {
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(LOCALE_STORAGE_KEY, locale)
  }
}

function updateDocumentLanguage(locale) {
  if (typeof document !== 'undefined') {
    document.documentElement.lang = getHtmlLang(locale)
  }
}

const initialLocale = normalizeLocale(readStoredLocale())
const state = reactive({ locale: initialLocale })

updateDocumentLanguage(initialLocale)

export function setLocale(locale) {
  const normalized = normalizeLocale(locale)
  state.locale = normalized
  persistLocale(normalized)
  updateDocumentLanguage(normalized)
}

export function translate(path, params = {}) {
  const localized = getNestedValue(messages[state.locale], path)
  const fallback = getNestedValue(messages[DEFAULT_LOCALE], path)
  return formatMessage(localized ?? fallback ?? path, params)
}

function replaceTerms(value, terms) {
  let output = String(value)
  const orderedTerms = Object.entries(terms || {}).sort((left, right) => right[0].length - left[0].length)

  for (const [source, target] of orderedTerms) {
    output = output.replaceAll(source, target)
  }

  return output
}

export function translateOptionName(name) {
  const value = String(name || '')
  if (!value || state.locale === DEFAULT_LOCALE) return value
  return replaceTerms(value, optionTermGlossaries[state.locale])
}

export function useLocale() {
  return {
    locale: computed(() => state.locale),
    localeState: readonly(state),
    supportedLocales: SUPPORTED_LOCALES,
    setLocale,
    t: translate,
    optionLabel: translateOptionName,
  }
}
