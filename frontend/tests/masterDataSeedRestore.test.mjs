import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const pageSource = await readFile(new URL('../src/modules/admin/pages/MasterDataPage.vue', import.meta.url), 'utf8')
const workspaceSource = await readFile(new URL('../src/modules/admin/composables/useMasterDataWorkspace.js', import.meta.url), 'utf8')
const apiSource = await readFile(new URL('../src/modules/admin/api/admin.js', import.meta.url), 'utf8')
const localeSource = await readFile(new URL('../src/locales/messages/masterData.js', import.meta.url), 'utf8')

test('master-data reset actions are real buttons and not passive status labels', () => {
  assert.ok(pageSource.includes('@click="restoreAllSeedDefaults"'))
  assert.ok(pageSource.includes("{{ t('masterData.restoreAllButton') }}"))
  assert.ok(pageSource.includes('@click="restoreCategory(selectedCategory)"'))
  assert.ok(pageSource.includes('@click="restoreOption(selectedOption)"'))
  assert.ok(pageSource.includes('@click="restoreShip(selectedShip)"'))
  assert.ok(pageSource.includes('type="button"'))
})

test('bulk reset uses a dedicated admin API with explicit confirmation', () => {
  assert.ok(apiSource.includes("post('/admin/master-data/restore-seed-defaults', {})"))
  assert.ok(workspaceSource.includes("window.confirm(t('masterData.restoreAllConfirm'))"))
  assert.ok(workspaceSource.includes('restoreAllMasterDataSeedDefaults()'))
  assert.ok(workspaceSource.includes("t('masterData.restoreAllSuccess'"))
})

test('all locales define the destructive reset copy', () => {
  for (const key of [
    'restoreAllKicker',
    'restoreAllTitle',
    'restoreAllHint',
    'restoreAllButton',
    'restoreAllConfirm',
    'restoreAllSuccess',
    'restoreAllError',
  ]) {
    assert.equal((localeSource.match(new RegExp(`${key}:`, 'g')) || []).length, 7, key)
  }
})
