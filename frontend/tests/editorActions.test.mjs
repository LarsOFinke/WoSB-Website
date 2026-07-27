import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { readGlobalStyles } from './helpers/readGlobalStyles.mjs'
import test from 'node:test'

const webhookPanel = readFileSync(new URL('../src/modules/admin/components/OutboundWebhookManagementPanel.vue', import.meta.url), 'utf8')
const mainCss = readGlobalStyles()
const buildEditor = readFileSync(new URL('../src/modules/builds/pages/BuildCreatePage.vue', import.meta.url), 'utf8')
const buildDesigner = readFileSync(new URL('../src/modules/builds/composables/useBuildDesigner.js', import.meta.url), 'utf8')

test('webhook editor is rendered in a body-level isolated drawer layer', () => {
  assert.match(webhookPanel, /<Teleport to="body">/)
  assert.match(webhookPanel, /<Transition name="webhook-editor">/)
  assert.match(webhookPanel, /class="webhook-editor-layer"/)
  assert.match(webhookPanel, /document\.body\.classList\.toggle\('webhook-editor-open'/)
  assert.match(mainCss, /\.webhook-editor-layer\s*\{[^}]*position:\s*fixed;[^}]*isolation:\s*isolate;/s)
  assert.match(mainCss, /body\.webhook-editor-open\s*\{[^}]*overflow:\s*hidden;/s)
  assert.match(mainCss, /\.webhook-active-toggle input\[type="checkbox"\][\s\S]*width:\s*1rem;/)
  assert.doesNotMatch(mainCss, /\.webhook-editor-actions\s*\{[^}]*position:\s*sticky;/s)
})

test('build editor exposes a guarded owner delete action', () => {
  assert.match(buildEditor, /v-if="isEditing"[\s\S]*@click="deleteBuild"/)
  assert.match(buildEditor, /:disabled="saving \|\| deleting"/)
  assert.match(buildDesigner, /import \{ createBuild, deleteMyBuild,/)
  assert.match(buildDesigner, /window\.confirm\(t\('myBuilds\.confirmDelete'\)\)/)
  assert.match(buildDesigner, /await deleteMyBuild\(props\.id\)/)
  assert.match(buildDesigner, /router\.replace\('\/profile\/builds'\)/)
})
