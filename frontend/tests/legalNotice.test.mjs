import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import { readCssBundle } from './helpers/readCssBundle.mjs'

import { legalNoticeMessages } from '../src/locales/messages/legalNotice.js'

const footer = readFileSync(new URL('../src/core/components/AppFooter.vue', import.meta.url), 'utf8')
const router = readFileSync(new URL('../src/router/index.js', import.meta.url), 'utf8')
const publicRoutes = readFileSync(new URL('../src/modules/legal/routes.js', import.meta.url), 'utf8')
const adminRoutes = readFileSync(new URL('../src/modules/admin/routes.js', import.meta.url), 'utf8')
const adminNavigation = readFileSync(new URL('../src/modules/admin/domain/staffNavigation.js', import.meta.url), 'utf8')
const publicPage = readFileSync(new URL('../src/modules/legal/pages/LegalNoticePage.vue', import.meta.url), 'utf8')
const adminPage = readFileSync(new URL('../src/modules/legal/pages/LegalNoticeAdminPage.vue', import.meta.url), 'utf8')
const api = readFileSync(new URL('../src/modules/legal/api/legalNotice.js', import.meta.url), 'utf8')

const shellStyles = readCssBundle([
  '../src/styles/global/40-shell-navigation.css',
  '../src/styles/global/40-shell-content-footer.css',
], import.meta.url)
const adminComposable = readFileSync(new URL('../src/modules/legal/composables/useLegalNoticeAdminPage.js', import.meta.url), 'utf8')
const generatedEnglish = readFileSync(new URL('../src/locales/generated/en.js', import.meta.url), 'utf8')


test('public legal notice is permanently reachable from the footer', () => {
  assert.ok(router.includes('...legalRoutes'))
  assert.ok(publicRoutes.includes("path: '/impressum'"))
  assert.ok(footer.includes('to="/impressum"'))
  assert.ok(footer.includes("legalNotice.public.footerLink"))
})


test('legal notice drafts stay hidden and published values render as text', () => {
  assert.ok(publicPage.includes('!notice.published'))
  assert.ok(publicPage.includes('notice.provider_name'))
  assert.ok(publicPage.includes('mailto:'))
  assert.ok(!publicPage.includes('v-html'))
  assert.ok(publicPage.includes('v-if="publicRepositoryUrl"'))
  assert.ok(publicPage.includes('rel="noopener noreferrer"'))
  assert.ok(publicPage.includes('legalNotice.public.repositoryLink'))
})


test('only administrators receive the legal notice editor', () => {
  assert.ok(adminRoutes.includes("path: '/admin/legal-notice'"))
  assert.ok(adminRoutes.includes('requiresAdmin: true'))
  assert.ok(adminNavigation.includes("key: 'legal-notice'"))
  assert.ok(adminPage.includes('form.published'))
  assert.ok(adminPage.includes('form.public_repository_url'))
  assert.ok(adminPage.includes('pattern="https://(?![^/]*@).*"'))
  assert.ok(adminPage.includes('resetToEnvironment'))
  assert.ok(api.includes("get('/admin/legal-notice')"))
  assert.ok(api.includes("put('/admin/legal-notice'"))
  assert.ok(api.includes("post('/admin/legal-notice/reset-environment'"))
  assert.ok(adminPage.includes('@click.prevent="resetToEnvironment"'))
  assert.ok(adminComposable.includes('hydrate(await resetAdminLegalNoticeToEnvironment())'))
})


test('legal notice copy exists for every supported locale', () => {
  for (const locale of ['en', 'de', 'fr', 'es', 'pt', 'ru', 'cn']) {
    assert.ok(legalNoticeMessages[locale]?.legalNotice?.public?.title, locale)
    assert.ok(legalNoticeMessages[locale]?.legalNotice?.admin?.legalWarningText, locale)
    assert.ok(legalNoticeMessages[locale]?.legalNotice?.fields?.providerName, locale)
    assert.ok(legalNoticeMessages[locale]?.legalNotice?.fields?.publicRepositoryUrl, locale)
    assert.ok(legalNoticeMessages[locale]?.legalNotice?.public?.repositoryText, locale)
  }
})


test('the German legal-page name remains Impressum in the default English interface', () => {
  assert.equal(legalNoticeMessages.en.legalNotice.public.title, 'Impressum')
  assert.equal(legalNoticeMessages.en.legalNotice.public.footerLink, 'Impressum')
  assert.equal(legalNoticeMessages.en.legalNotice.admin.title, 'Impressum')
  assert.equal(legalNoticeMessages.en.legalNotice.admin.navigation, 'Impressum')
  assert.ok(generatedEnglish.includes('\"footerLink\":\"Impressum\"'))
  assert.ok(generatedEnglish.includes('\"navigation\":\"Impressum\"'))
})


test('the application shell keeps the footer at the viewport bottom on short pages', () => {
  assert.ok(shellStyles.includes('min-height: 100dvh'))
  assert.ok(shellStyles.includes('grid-template-rows: auto minmax(0, 1fr) auto'))
  assert.ok(shellStyles.includes('align-self: end'))
  assert.ok(shellStyles.includes('"sidebar footer"'))
  assert.equal(shellStyles.includes('"footer footer"'), false)
  assert.ok(footer.includes('class="wire-section app-footer"'))
})
