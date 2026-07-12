import test from 'node:test'
import assert from 'node:assert/strict'

import { buildPrintFileName, createBuildPrintModel, createBuildPrintSvg } from '../src/modules/builds/buildPrintExport.js'

const translations = {
  'builds.statLabels.durability': 'Durability',
  'builds.statLabels.speed_knots': 'Speed',
  'builds.statLabels.maneuverability': 'Maneuverability',
  'builds.statLabels.armor': 'Armor',
  'builds.statLabels.hold_capacity': 'Hold',
  'builds.statLabels.crew_capacity': 'Crew capacity',
  'builds.statLabels.sailor_minimum': 'Sailor minimum',
  'builds.statLabels.displacement_tons': 'Displacement',
  'builds.types.balanced': 'Balanced',
  'builds.detail.buildType': 'Build type',
  'builds.detail.shipStats': 'Ship stats',
  'builds.detail.weaponCapacity': 'Capacity {count}',
  'builds.detail.crewDistribution': 'Crew distribution',
  'builds.commandDeck.crewRemaining': '{value} crew remaining',
  'common.rate': 'Rate',
  'builds.list.upgradeSummary': '{used}/{max} upgrades',
  'builds.detail.weapons.front': 'Front weapons',
  'builds.detail.weapons.port': 'Port weapons',
  'builds.detail.weapons.starboard': 'Starboard weapons',
  'builds.detail.weapons.rear': 'Rear weapons',
  'builds.detail.weapons.mortar': 'Mortar weapons',
  'builds.detail.weapons.special': 'Special weapons',
  'builds.detail.noDetails': 'No details',
  'builds.create.crew.sailors': 'Sailors',
  'builds.create.crew.musketeers': 'Musketeers',
  'builds.create.crew.soldiers': 'Soldiers',
  'builds.create.crew.mercenaries': 'Mercenaries',
  'builds.list.sailorMin': 'Min {value}',
  'builds.detail.sail': 'Sail',
  'builds.detail.lantern': 'Lantern',
  'builds.detail.researchUpgradeSlot': 'Research slot',
  'builds.detail.researchUpgradeSlotActive': 'Unlocked',
  'builds.detail.researchUpgradeSlotInactive': 'Locked',
  'builds.commandDeck.performanceEyebrow': 'Performance',
  'builds.commandDeck.performanceTitle': 'Ship performance',
  'builds.crewConsole.eyebrow': 'Crew operations',
  'builds.commandDeck.configurationEyebrow': 'Configuration',
  'builds.detail.upgrades': 'Upgrades',
  'builds.detail.specialCrew': 'Special crew',
  'builds.detail.inventory': 'Inventory',
  'builds.detail.ammunition': 'Ammunition',
  'builds.detail.consumables': 'Consumables',
  'builds.detail.hold': 'Hold',
  'builds.detail.details': 'Details',
  'builds.print.eyebrow': 'Offline build sheet',
  'builds.print.fallbackTitle': 'Build sheet',
  'builds.print.preparedAt': 'Prepared {value}',
  'builds.print.configurationTitle': 'Configuration snapshot',
  'builds.print.weaponLoadoutTitle': 'Weapon loadout',
  'builds.print.inventoryTitle': 'Ammunition and hold',
  'builds.print.notesTitle': 'Captain notes',
  'builds.print.footerHint': 'Prepared from the live build designer for offline review and print distribution.',
  'builds.print.footerBrand': 'Royal Blackwater Fleet · Build Designer',
}

function t(key, params = {}) {
  const template = translations[key] || key
  return Object.entries(params).reduce((acc, [name, value]) => acc.replaceAll(`{${name}}`, value), template)
}

const build = {
  id: 42,
  build_name: 'Leopard Event Build',
  build_type: 'balanced',
  sails: 'Raiding Sails',
  lantern: 'Ice Lantern',
  research_upgrade_slot_unlocked: true,
  sailors: 80,
  musketeers: 10,
  soldiers: 30,
  mercenaries: 5,
  upgrade_1: 'Copper Sheathing',
  upgrade_2: 'Trim',
  ship: {
    name: 'Leopard',
    rate: 'III',
    ship_type: 'Medium',
    crew_capacity: 160,
    sailor_minimum: 80,
  },
  ship_stats: {
    crew_total: 125,
    crew_capacity: 160,
    crew_remaining: 35,
    weapon_total: 29,
    weapon_capacity_total: 29,
    upgrade_slots_available: 5,
    sailor_minimum: 80,
    stat_rows: [
      { key: 'durability', base: 2040, effective: 2142, modifier: 5, modifier_kind: 'percent', precision: 0 },
      { key: 'speed_knots', base: 9.6, effective: 10.1, modifier: 5, modifier_kind: 'percent', precision: 1 },
    ],
  },
  front_weapon_slots: [{ item: 'Bow Chaser', quantity: 2 }],
  port_weapon_slots: [{ item: 'Long 18-pdr', quantity: 12 }],
  starboard_weapon_slots: [{ item: 'Long 18-pdr', quantity: 12 }],
  rear_weapon_slots: [{ item: 'Stern Chaser', quantity: 3 }],
  special_crew_slots: [{ item: 'Doctor', quantity: 1 }],
  ammunition_slots: [{ item: 'Round Shot', quantity: 200 }],
  consumable_slots: [{ item: 'Repair Kit', quantity: 3 }],
  hold_slots: [{ item: 'Oak Logs', quantity: 50 }],
  details: 'Prepared for the current event and tuned for speed with a balanced broadside.',
}

test('build print model exposes export-ready sections', () => {
  const model = createBuildPrintModel(build, { t, optionLabel: (value) => value, locationObject: { origin: 'https://fleet.example' } })
  assert.equal(model.buildName, 'Leopard Event Build')
  assert.equal(model.shipName, 'Leopard')
  assert.equal(model.shareUrl, 'https://fleet.example/builds/42')
  assert.deepEqual(model.upgrades, ['Copper Sheathing', 'Trim'])
  assert.equal(model.weapons[1].lines[0], 'Long 18-pdr ×12')
})

test('build print svg contains the key build identifiers', () => {
  const svg = createBuildPrintSvg(build, { t, optionLabel: (value) => value, locationObject: { origin: 'https://fleet.example' } })
  assert.match(svg, /Leopard Event Build/)
  assert.match(svg, /https:\/\/fleet\.example\/builds\/42/)
  assert.match(svg, /Weapon loadout/)
  assert.match(svg, /Copper Sheathing/)
})

test('build print file names are sanitized for downloads', () => {
  assert.equal(buildPrintFileName({ build_name: 'Santisima Trinidad #1' }, 'png'), 'santisima-trinidad-1-build-sheet.png')
})
