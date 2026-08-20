import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const page = readFileSync(new URL('../src/modules/onboarding/pages/NewcomerGuidePage.vue', import.meta.url), 'utf8')
const navigation = readFileSync(new URL('../src/modules/onboarding/components/NewcomerFolderNavigation.vue', import.meta.url), 'utf8')
const editor = readFileSync(new URL('../src/modules/onboarding/components/NewcomerFolderEditor.vue', import.meta.url), 'utf8')
const resourceEditor = readFileSync(new URL('../src/modules/onboarding/components/NewcomerResourceEditor.vue', import.meta.url), 'utf8')
const explorer = readFileSync(new URL('../src/modules/onboarding/components/NewcomerTopicExplorer.vue', import.meta.url), 'utf8')

test('new captain guide separates a readable journey from the maintainer workspace', () => {
  assert.match(page, /NewcomerFolderNavigation/)
  assert.match(page, /NewcomerTopicExplorer/)
  assert.match(page, /editable/)
  assert.match(navigation, /<nav/)
  assert.match(navigation, /aria-current/)
  assert.match(navigation, /@click="\$emit\('move'/)
  assert.match(editor, /resourceOrderHint/)
  assert.match(editor, /NewcomerResourceEditor/)
  assert.match(resourceEditor, /<details/)
  assert.match(explorer, /newcomer-explorer-address/)
  assert.match(explorer, /newcomer-explorer-search/)
  assert.match(explorer, /newcomer-topic-grid/)
  assert.match(explorer, /newcomer-reader-article/)
  assert.match(explorer, /newcomer-mobile-topic-picker/)
  assert.match(explorer, /newcomer-topic-progress/)
  assert.match(explorer, /NewcomerFolderContent/)
  assert.doesNotMatch(explorer, /selectedResourceIndex/)
  assert.doesNotMatch(page, /v-for="\(block, blockIndex\) in draft\.blocks"/)
  assert.doesNotMatch(page, /addLinkedResource/)
})
