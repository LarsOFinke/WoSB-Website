const ammunitionVisual = new URL('../../assets/build-visuals/ammunition.svg', import.meta.url).href
const consumableVisual = new URL('../../assets/build-visuals/consumable.svg', import.meta.url).href
const mercenariesVisual = new URL('../../assets/build-visuals/crew-mercenaries.svg', import.meta.url).href
const musketeersVisual = new URL('../../assets/build-visuals/crew-musketeers.svg', import.meta.url).href
const sailorsVisual = new URL('../../assets/build-visuals/crew-sailors.svg', import.meta.url).href
const soldiersVisual = new URL('../../assets/build-visuals/crew-soldiers.svg', import.meta.url).href
const holdVisual = new URL('../../assets/build-visuals/hold.svg', import.meta.url).href
const lanternVisual = new URL('../../assets/build-visuals/lantern.svg', import.meta.url).href
const sailVisual = new URL('../../assets/build-visuals/sail.svg', import.meta.url).href
const shipVisual = new URL('../../assets/build-visuals/ship.svg', import.meta.url).href
const specialistVisual = new URL('../../assets/build-visuals/specialist.svg', import.meta.url).href
const upgradeVisual = new URL('../../assets/build-visuals/upgrade.svg', import.meta.url).href
const weaponVisual = new URL('../../assets/build-visuals/weapon.svg', import.meta.url).href

export const BUILD_ASSET_MODES = Object.freeze({
  NEUTRAL: 'neutral',
  GAME: 'game',
})

const configuredAssetMode = import.meta.env?.VITE_BUILD_ASSET_MODE
export const buildAssetMode = configuredAssetMode === BUILD_ASSET_MODES.GAME
  ? BUILD_ASSET_MODES.GAME
  : BUILD_ASSET_MODES.NEUTRAL
export const isGameAssetMode = buildAssetMode === BUILD_ASSET_MODES.GAME

export const BUILD_VISUAL_URLS = Object.freeze({
  ammunition: ammunitionVisual,
  consumable: consumableVisual,
  'crew-mercenaries': mercenariesVisual,
  'crew-musketeers': musketeersVisual,
  'crew-sailors': sailorsVisual,
  'crew-soldiers': soldiersVisual,
  hold: holdVisual,
  lantern: lanternVisual,
  sail: sailVisual,
  ship: shipVisual,
  specialist: specialistVisual,
  upgrade: upgradeVisual,
  weapon: weaponVisual,
})

export const buildCategoryVisuals = Object.freeze({
  ship: BUILD_VISUAL_URLS.ship,
  sail: BUILD_VISUAL_URLS.sail,
  upgrade: BUILD_VISUAL_URLS.upgrade,
  lantern: BUILD_VISUAL_URLS.lantern,
  weapon: BUILD_VISUAL_URLS.weapon,
  special_crew: BUILD_VISUAL_URLS.specialist,
  specialist: BUILD_VISUAL_URLS.specialist,
  ammunition: BUILD_VISUAL_URLS.ammunition,
  consumable: BUILD_VISUAL_URLS.consumable,
  hold: BUILD_VISUAL_URLS.hold,
})

export const buildCrewVisuals = Object.freeze({
  sailors: BUILD_VISUAL_URLS['crew-sailors'],
  musketeers: BUILD_VISUAL_URLS['crew-musketeers'],
  soldiers: BUILD_VISUAL_URLS['crew-soldiers'],
  mercenaries: BUILD_VISUAL_URLS['crew-mercenaries'],
})

export function buildVisualUrl(key, fallback = '') {
  return BUILD_VISUAL_URLS[key] ?? fallback
}

export function buildCategoryVisualUrl(categoryKey, fallback = '') {
  return buildCategoryVisuals[categoryKey] ?? fallback
}

export function buildCrewVisualUrl(roleKey, fallback = '') {
  return buildCrewVisuals[roleKey] ?? fallback
}

function isGameAssetUrl(imageUrl) {
  return String(imageUrl || '').includes('/build-assets/game/')
}

export function buildOptionVisual(imageUrl, categoryKey, fallback = '') {
  const neutralVisual = buildCategoryVisuals[categoryKey] ?? fallback
  if (isGameAssetMode && imageUrl && isGameAssetUrl(imageUrl)) return imageUrl
  if (!isGameAssetMode && isGameAssetUrl(imageUrl)) return neutralVisual
  return imageUrl || neutralVisual
}
