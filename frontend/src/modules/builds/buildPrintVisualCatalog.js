import { buildCrewVisualUrl, buildVisualUrl } from './buildVisuals.js'

export const BUILD_PRINT_RENDERER_VERSION = '3'

export const BUILD_PRINT_THEMES = Object.freeze({
  dark: Object.freeze({
    page: '#07111a', panel: '#0d1a26', panelSoft: '#112231', border: '#263847',
    borderStrong: '#8f713f', text: '#f4f7fa', muted: '#9babb9', faint: '#647889',
    accent: '#e8be70', accentSoft: '#2c281f', danger: '#d88980',
  }),
  light: Object.freeze({
    page: '#f8fafc', panel: '#ffffff', panelSoft: '#f1f4f7', border: '#c7d0d9',
    borderStrong: '#a87516', text: '#10243d', muted: '#526170', faint: '#748391',
    accent: '#94620b', accentSoft: '#fbf4e5', danger: '#a6413a',
  }),
})

export const PRINT_VISUALS = Object.freeze({
  ship: buildVisualUrl('ship'),
  sail: buildVisualUrl('sail'),
  lantern: buildVisualUrl('lantern'),
  upgrade: buildVisualUrl('upgrade'),
  weapon: buildVisualUrl('weapon'),
  specialist: buildVisualUrl('specialist'),
  ammunition: buildVisualUrl('ammunition'),
  consumable: buildVisualUrl('consumable'),
  hold: buildVisualUrl('hold'),
  notes: buildVisualUrl('specialist'),
  crew: Object.freeze({
    sailors: buildCrewVisualUrl('sailors'),
    musketeers: buildCrewVisualUrl('musketeers'),
    soldiers: buildCrewVisualUrl('soldiers'),
    mercenaries: buildCrewVisualUrl('mercenaries'),
  }),
})
