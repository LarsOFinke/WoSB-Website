import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const page = readFileSync(new URL('../src/modules/onboarding/pages/NewcomerGuidePage.vue', import.meta.url), 'utf8')
const navigation = readFileSync(new URL('../src/modules/onboarding/components/NewcomerFolderNavigation.vue', import.meta.url), 'utf8')
const editor = readFileSync(new URL('../src/modules/onboarding/components/NewcomerFolderEditor.vue', import.meta.url), 'utf8')

test('new captain guide uses one ordered folder browser for readers and moderators', () => {
  assert.match(page, /NewcomerFolderNavigation/)
  assert.match(page, /:folder="activeFolder"/)
  assert.match(page, /editable/)
  assert.match(navigation, /<nav/)
  assert.match(navigation, /aria-current/)
  assert.match(navigation, /@click="\$emit\('move'/)
  assert.match(editor, /resourceOrderHint/)
  assert.doesNotMatch(page, /v-for="\(block, blockIndex\) in draft\.blocks"/)
})
