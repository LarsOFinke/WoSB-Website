import { computed, reactive, readonly } from 'vue'

import { DEFAULT_LOCALE, SUPPORTED_LOCALES } from './config'
import englishLocale from './generated/en.js'
import { formatMessage, getNestedValue } from './utils'

export { DEFAULT_LOCALE, SUPPORTED_LOCALES }

const LOCALE_STORAGE_KEY = 'rbf-hub.locale'
const LEGACY_LOCALE_STORAGE_KEYS = ['rbv-hub.locale', 'blackwater-hub.locale']
const localeLoaders = {
  cn: () => import('./generated/cn.js'),
  de: () => import('./generated/de.js'),
  es: () => import('./generated/es.js'),
  fr: () => import('./generated/fr.js'),
  pt: () => import('./generated/pt.js'),
  ru: () => import('./generated/ru.js'),
}
const loadedLocales = { en: englishLocale }
const pendingLocales = new Map()
let localeRequest = 0
let localeChangeHandler = null

function normalizeLocale(locale) {
  return SUPPORTED_LOCALES.some((entry) => entry.code === locale) ? locale : DEFAULT_LOCALE
}

function getHtmlLang(locale) {
  return SUPPORTED_LOCALES.find((entry) => entry.code === locale)?.htmlLang || 'en'
}

function readStoredLocale() {
  if (typeof localStorage === 'undefined') return DEFAULT_LOCALE
  const stored = localStorage.getItem(LOCALE_STORAGE_KEY) || LEGACY_LOCALE_STORAGE_KEYS.map((key) => localStorage.getItem(key)).find(Boolean)
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

const requestedLocale = normalizeLocale(readStoredLocale())
const state = reactive({ locale: DEFAULT_LOCALE, loadingLocale: null })

updateDocumentLanguage(DEFAULT_LOCALE)

async function loadLocale(locale) {
  if (loadedLocales[locale]) return loadedLocales[locale]
  if (!localeLoaders[locale]) return loadedLocales[DEFAULT_LOCALE]
  if (!pendingLocales.has(locale)) {
    pendingLocales.set(locale, localeLoaders[locale]().then((module) => {
      loadedLocales[locale] = module.default
      pendingLocales.delete(locale)
      return module.default
    }).catch((error) => {
      pendingLocales.delete(locale)
      throw error
    }))
  }
  return pendingLocales.get(locale)
}

export async function setLocale(locale) {
  const normalized = normalizeLocale(locale)
  const request = ++localeRequest
  state.loadingLocale = normalized
  try {
    await loadLocale(normalized)
  } catch (error) {
    if (request === localeRequest) console.error(`Could not load locale '${normalized}'.`, error)
    return false
  } finally {
    if (request === localeRequest) state.loadingLocale = null
  }
  if (request !== localeRequest) return false
  state.locale = normalized
  persistLocale(normalized)
  updateDocumentLanguage(normalized)
  localeChangeHandler?.(normalized)
  return true
}

export function onLocaleChange(handler) {
  localeChangeHandler = typeof handler === 'function' ? handler : null
}

export async function initializeLocale() {
  return setLocale(requestedLocale)
}

export function translate(path, params = {}) {
  const localized = getNestedValue(loadedLocales[state.locale]?.messages, path)
  const fallback = getNestedValue(loadedLocales[DEFAULT_LOCALE].messages, path)
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
  return replaceTerms(value, loadedLocales[state.locale]?.optionTerms)
}

export function useLocale() {
  return {
    locale: computed(() => state.locale),
    localeLoading: computed(() => state.loadingLocale),
    localeState: readonly(state),
    supportedLocales: SUPPORTED_LOCALES,
    setLocale,
    t: translate,
    optionLabel: translateOptionName,
  }
}
