import assert from 'node:assert/strict'
import { existsSync, readFileSync, readdirSync } from 'node:fs'
import test from 'node:test'
import { buildAssetMode, buildOptionVisual } from '../src/modules/builds/buildVisuals.js'

const buildEditor = readFileSync(new URL('../src/modules/builds/pages/BuildCreatePage.vue', import.meta.url), 'utf8')
const picker = readFileSync(new URL('../src/modules/builds/components/BuildOptionPicker.vue', import.meta.url), 'utf8')
const pickerCss = readFileSync(new URL('../src/modules/builds/styles/buildOptionPicker.css', import.meta.url), 'utf8')

function catalog(name) {
  const directory = new URL(`../../spring-api/src/main/resources/seed/builds/options/${name}/`, import.meta.url)
  return readdirSync(directory)
    .filter(filename => filename.endsWith('.json'))
    .sort()
    .map(filename => JSON.parse(readFileSync(new URL(filename, directory), 'utf8')))
}

function publicAsset(imageUrl) {
  return new URL(`../public/${String(imageUrl).replace(/^\//, '')}`, import.meta.url)
}

function gameAsset(imageUrl) {
  return new URL(`../${String(imageUrl).replace(/^\/build-assets\/game\//, 'game-assets/')}`, import.meta.url)
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

test('catalog visual paths are separated into neutral and game asset trees', () => {
  for (const filename of ['sails', 'upgrades', 'lanterns', 'specialists']) {
    const rows = catalog(filename)
    assert.ok(rows.length > 0)
    for (const row of rows) {
      const expectedTree = ['upgrades', 'specialists'].includes(filename) ? 'game' : 'neutral'
      assert.match(row.image_url, new RegExp(`^/build-assets/${expectedTree}/options/`))
      const asset = expectedTree === 'game' ? gameAsset(row.image_url) : publicAsset(row.image_url)
      assert.equal(existsSync(asset), true, `${filename}: ${row.name}`)
    }
  }
})

test('neutral mode replaces game-derived specialist and upgrade imagery', () => {
  assert.equal(buildAssetMode, 'neutral')
  assert.match(buildOptionVisual('/build-assets/game/options/specialists/corsair.png', 'special_crew'), /specialist\.svg$/)
  assert.match(buildOptionVisual('/build-assets/game/options/upgrades/iron-plating.png', 'upgrade'), /upgrade\.svg$/)
  assert.match(buildOptionVisual('/build-assets/neutral/options/sails/cheap.svg', 'sail'), /cheap\.svg$/)
})
