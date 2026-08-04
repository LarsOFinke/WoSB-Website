import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import test from 'node:test'

const buildEditor = readFileSync(new URL('../src/modules/builds/pages/BuildCreatePage.vue', import.meta.url), 'utf8')
const picker = readFileSync(new URL('../src/modules/builds/components/BuildOptionPicker.vue', import.meta.url), 'utf8')
const pickerCss = readFileSync(new URL('../src/modules/builds/styles/buildOptionPicker.css', import.meta.url), 'utf8')

function catalog(name) {
  return JSON.parse(readFileSync(new URL(`../../spring-api/src/main/resources/seed/builds/options/${name}.json`, import.meta.url), 'utf8'))
}

function publicAsset(imageUrl) {
  return new URL(`../public/${String(imageUrl).replace(/^\//, '')}`, import.meta.url)
}

test('build editor uses an icon-aware option picker for equipment and specialists', () => {
  assert.match(buildEditor, /import BuildOptionPicker/)
  assert.match(buildEditor, /v-model="form\.sails"[\s\S]*:options="sailPickerOptions"/)
  assert.match(buildEditor, /v-model="form\[`upgrade_\$\{index\}`\]"[\s\S]*:groups="upgradePickerGroups\(index\)"/)
  assert.match(buildEditor, /:options="specialistPickerOptions\(index\)"/)
  assert.match(buildEditor, /meta: formatEffects\(name, categoryKey\)/)
  assert.match(picker, /role="combobox"/)
  assert.match(picker, /role="listbox"/)
  assert.match(picker, /<img v-if="option\.image"/)
  assert.match(picker, /<small v-if="option\.meta">\{\{ option\.meta \}\}<\/small>/)
  assert.match(pickerCss, /\.build-option-picker-menu\s*\{[\s\S]*max-height:/)
})

test('every screenshot-backed visual catalog item resolves to a committed public asset', () => {
  for (const filename of ['sails', 'upgrades', 'lanterns', 'specialists']) {
    const rows = catalog(filename).items
    assert.ok(rows.length > 0)
    for (const row of rows) {
      assert.match(row.image_url, /^\/build-assets\/options\//)
      assert.equal(existsSync(publicAsset(row.image_url)), true, `${filename}: ${row.name}`)
    }
  }
})
