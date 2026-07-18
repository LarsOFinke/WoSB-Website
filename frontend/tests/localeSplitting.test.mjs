import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

async function source(path) {
  return readFile(new URL(path, import.meta.url), 'utf8')
}

test('non-default locales remain lazy runtime chunks', async () => {
  const localeRuntime = await source('../src/locales/index.js')
  const main = await source('../src/main.js')
  const router = await source('../src/router/index.js')
  const viteConfig = await source('../vite.config.js')

  assert.ok(localeRuntime.includes("import englishLocale from './generated/en.js'"))
  for (const locale of ['cn', 'de', 'es', 'fr', 'pt', 'ru']) {
    assert.ok(localeRuntime.includes(`${locale}: () => import('./generated/${locale}.js')`))
    assert.ok(!localeRuntime.includes(`import ${locale}Locale from './generated/${locale}.js'`))
  }
  assert.ok(!localeRuntime.includes("from './messages'"))
  assert.ok(main.includes('await initializeLocale()'))
  assert.ok(router.includes('onLocaleChange(() => updateDocumentTitle(router.currentRoute.value))'))
  assert.ok(!viteConfig.includes("name: 'app-locales'"))
})

test('locale generation runs before development, tests, and production builds', async () => {
  const packageJson = JSON.parse(await source('../package.json'))

  assert.match(packageJson.scripts.predev, /locales:generate/)
  assert.match(packageJson.scripts.pretest, /locales:generate/)
  assert.match(packageJson.scripts.prebuild, /locales:generate/)
})
