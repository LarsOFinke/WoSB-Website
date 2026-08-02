import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import { readCssBundle } from './helpers/readCssBundle.mjs'

const webhookPanel = readFileSync(new URL('../src/modules/admin/components/OutboundWebhookManagementPanel.vue', import.meta.url), 'utf8')
const adminIntegrationsCss = readCssBundle([
  '../src/modules/admin/styles/adminWebhookConfiguration.css',
  '../src/modules/admin/styles/adminWebhookEditorDrawer.css',
], import.meta.url)
const buildEditor = readFileSync(new URL('../src/modules/builds/pages/BuildCreatePage.vue', import.meta.url), 'utf8')
const buildDesigner = readFileSync(new URL('../src/modules/builds/composables/useBuildDesigner.js', import.meta.url), 'utf8')

test('webhook editor is rendered in a body-level isolated drawer layer', () => {
  assert.match(webhookPanel, /<Teleport to="body">/)
  assert.match(webhookPanel, /<Transition name="webhook-editor">/)
  assert.match(webhookPanel, /class="webhook-editor-layer"/)
  assert.match(webhookPanel, /document\.body\.classList\.toggle\('webhook-editor-open'/)
  assert.match(adminIntegrationsCss, /\.webhook-editor-layer\s*\{[^}]*position:\s*fixed;[^}]*isolation:\s*isolate;/s)
  assert.match(adminIntegrationsCss, /body\.webhook-editor-open\s*\{[^}]*overflow:\s*hidden;/s)
  assert.match(adminIntegrationsCss, /\.webhook-editor\s*\{[^}]*grid-auto-rows:\s*max-content;/s)
  assert.match(adminIntegrationsCss, /\.webhook-active-toggle input\[type="checkbox"\][\s\S]*width:\s*1rem;/)
  assert.doesNotMatch(adminIntegrationsCss, /\.webhook-editor-actions\s*\{[^}]*position:\s*sticky;/s)
})

test('build editor exposes a guarded owner delete action', () => {
  assert.match(buildEditor, /v-if="isEditing"[\s\S]*@click="deleteBuild"/)
  assert.match(buildEditor, /:disabled="saving \|\| deleting"/)
  assert.match(buildDesigner, /import \{ createBuild, deleteMyBuild,/)
  assert.match(buildDesigner, /window\.confirm\(t\('myBuilds\.confirmDelete'\)\)/)
  assert.match(buildDesigner, /await deleteMyBuild\(props\.id\)/)
  assert.match(buildDesigner, /router\.replace\('\/profile\/builds'\)/)
})
