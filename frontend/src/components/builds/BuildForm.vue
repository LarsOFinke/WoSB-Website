<template>
  <form class="build-form" @submit.prevent="submitForm">
    <p class="muted">
      Der Build-Designer nutzt den geseedeten Backend-Katalog für Schiffe, Upgrades, Kanonen, Munition,
      Verbrauchsgüter und Crew-Bausteine. Schiffsdaten werden separat angezeigt, damit Rate/Klasse nicht doppelt wirken.
    </p>

    <div class="form-row">
      <label for="buildTitle">Titel</label>
      <input id="buildTitle" v-model.trim="form.title" class="input" required maxlength="100" placeholder="z. B. Victory Linienbrecher" />
    </div>

    <div class="grid grid-2 compact-form-grid">
      <div class="form-row">
        <label for="buildShip">Schiff aus Katalog</label>
        <select id="buildShip" v-model="shipSelection" class="select">
          <option value="">Kein konkretes Schiff / allgemeines Build</option>
          <option v-for="ship in ships" :key="ship.id" :value="String(ship.id)">
            {{ shipOptionLabel(ship) }}
          </option>
        </select>
      </div>

      <div class="form-row">
        <label for="buildShipClass">Fallback-Schiffsklasse</label>
        <select id="buildShipClass" v-model="form.ship_class" class="select" :disabled="Boolean(selectedShip)">
          <option v-for="shipClass in shipClassOptions" :key="shipClass" :value="shipClass">{{ shipClass }}</option>
        </select>
      </div>
    </div>

    <div v-if="selectedShip" class="ship-build-summary separated-ship-facts">
      <span class="badge">Rate {{ selectedShipRate || selectedShip.rate }}</span>
      <span class="badge subtle-badge">{{ selectedShip.progression_class }}</span>
      <span>{{ selectedShip.ship_class }}</span>
      <span>Speed {{ selectedShip.speed ?? '—' }}</span>
      <span>Agilität {{ selectedShip.agility ?? '—' }}</span>
      <span>Crew {{ selectedShip.crew ?? '—' }}</span>
      <span>Laderaum {{ selectedShip.hold_capacity ?? '—' }}</span>
    </div>

    <div class="grid grid-2 compact-form-grid">
      <div class="form-row">
        <label for="buildPurpose">Einsatzbereich</label>
        <select id="buildPurpose" v-model="form.purpose" class="select">
          <option v-for="purpose in buildPurposeOptions" :key="purpose" :value="purpose">{{ purpose }}</option>
        </select>
      </div>

      <div class="form-row">
        <label for="buildRole">Build-Rolle optional</label>
        <select id="buildRole" v-model="form.build_role" class="select">
          <option value="">Keine feste Rolle</option>
          <option v-for="role in buildRoleOptions" :key="role" :value="role">{{ role }}</option>
        </select>
      </div>
    </div>

    <section class="setup-section designer-panel">
      <div class="setup-section-header">
        <div>
          <h3>Bewaffnung nach Position</h3>
          <p class="muted">Plane Bug, Backbord, Steuerbord und Heck getrennt. Das ist für Chaser, Breitseiten und Rückzugsdruck übersichtlicher.</p>
        </div>
        <select class="select preset-select" @change="appendOption($event, 'cannon_setup')">
          <option value="">Allgemeine Waffen-Notiz hinzufügen</option>
          <option v-for="option in optionsFor('cannon')" :key="option.id" :value="optionLabel(option)">{{ optionLabel(option) }}</option>
        </select>
      </div>

      <div class="weapon-position-grid">
        <div v-for="position in weaponPositions" :key="position.field" class="weapon-position-card">
          <div class="weapon-position-header">
            <span class="badge">{{ position.label }}</span>
            <span class="muted">{{ position.hint }}</span>
          </div>
          <select class="select" @change="setWeaponPosition($event, position.field, position.label)">
            <option value="">Waffentyp wählen</option>
            <option v-for="option in optionsFor('cannon')" :key="`${position.field}-${option.id}`" :value="optionLabel(option)">{{ optionLabel(option) }}</option>
          </select>
          <textarea
            v-model.trim="form[position.field]"
            class="textarea compact-textarea"
            :placeholder="position.placeholder"
            maxlength="4000"
          />
        </div>
      </div>

      <label class="form-row">
        <span>Allgemeine Waffen-Notiz</span>
        <textarea v-model.trim="form.cannon_setup" class="textarea compact-textarea" placeholder="z. B. Reichweite priorisieren, Bug/Heck nur als Chaser, Breitseiten identisch halten ..." />
      </label>
    </section>

    <div class="build-designer-grid">
      <section class="setup-section designer-panel">
        <div class="setup-section-header">
          <div>
            <h3>Segel-Slot</h3>
            <p class="muted">Seit Update B17 hat jedes neu gebaute Schiff einen Segel-Slot.</p>
          </div>
          <select class="select preset-select" @change="appendOption($event, 'sail_setup')">
            <option value="">Segel hinzufügen</option>
            <option v-for="option in optionsFor('sail')" :key="option.id" :value="optionLabel(option)">{{ optionLabel(option) }}</option>
          </select>
        </div>
        <textarea v-model.trim="form.sail_setup" class="textarea" placeholder="Segel-Setup und Einsatzfenster ..." />
      </section>

      <section class="setup-section designer-panel">
        <div class="setup-section-header">
          <div>
            <h3>Spezialcrew</h3>
            <p class="muted">Spezialcrew als Slots/Notizen sammeln.</p>
          </div>
          <select class="select preset-select" @change="appendOption($event, 'special_crew_setup')">
            <option value="">Spezialcrew hinzufügen</option>
            <option v-for="option in optionsFor('special_crew')" :key="option.id" :value="optionLabel(option)">{{ optionLabel(option) }}</option>
          </select>
        </div>
        <textarea v-model.trim="form.special_crew_setup" class="textarea" placeholder="Spezialcrew, Synergien, Alternativen ..." />
      </section>
    </div>

    <section class="setup-section designer-panel">
      <div class="setup-section-header">
        <div>
          <h3>Upgrade-Slots</h3>
          <p class="muted">Slot 1–2 sind Basis, Slot 3–4 per XP, Spezialslot als späteres Feintuning.</p>
        </div>
        <button class="button small secondary" type="button" @click="applyUpgradeSlots">Slots in Setup übernehmen</button>
      </div>

      <div class="upgrade-slot-grid">
        <div v-for="(slot, index) in upgradeSlots" :key="index" class="form-row mini-form-row">
          <label :for="`upgradeSlot${index}`">{{ slot.label }}</label>
          <select :id="`upgradeSlot${index}`" v-model="slot.value" class="select">
            <option value="">Kein Upgrade</option>
            <option v-for="option in optionsFor(slot.category)" :key="option.id" :value="optionLabel(option)">{{ optionLabel(option) }}</option>
          </select>
        </div>
      </div>

      <textarea v-model.trim="form.upgrade_setup" class="textarea" placeholder="Upgrade-Plan wird hier gesammelt ..." />
    </section>

    <section class="setup-section designer-panel">
      <div class="setup-section-header">
        <div>
          <h3>Crew-Verteilung</h3>
          <p class="muted">Vier Kategorien per Schieberegler. Summe und Schiffslimit bleiben sichtbar, damit der Plan plausibel bleibt.</p>
        </div>
        <select class="select preset-select" @change="applyCrewPreset($event)">
          <option value="">Crew-Preset anwenden</option>
          <option value="balanced">Ausgewogen</option>
          <option value="gunnery">Kanoniere / Reload</option>
          <option value="sailing">Segel / Mobilität</option>
          <option value="repair">Reparatur / Sustain</option>
          <option value="boarding">Boarding / Nahkampf</option>
        </select>
      </div>

      <div class="crew-toolbar">
        <div class="form-row mini-form-row">
          <label for="crewTarget">Geplante Crew-Anzahl</label>
          <input
            id="crewTarget"
            v-model.number="form.crew_target"
            class="input"
            type="number"
            min="0"
            :max="selectedShip?.crew || 500"
            :placeholder="selectedShip?.crew ? `Max. ${selectedShip.crew}` : 'Optional'"
            @change="normalizeCrewAfterTargetChange"
          />
        </div>
        <button class="button secondary" type="button" :disabled="!selectedShip?.crew" @click="fillMaxCrew">Max-Crew übernehmen</button>
        <span :class="['crew-balance-badge', crewDeltaClass]">
          {{ crewBalanceText }}
        </span>
      </div>

      <div class="crew-slider-grid">
        <label v-for="category in crewCategories" :key="category.key" class="crew-slider-card">
          <span class="crew-slider-header">
            <strong>{{ category.label }}</strong>
            <span>{{ form[category.key] || 0 }}</span>
          </span>
          <input
            v-model.number="form[category.key]"
            class="range"
            type="range"
            min="0"
            :max="crewSliderMax"
            step="1"
            @input="clampCrew(category.key)"
          />
          <small class="muted">{{ category.hint }}</small>
        </label>
      </div>

      <div class="setup-section-header compact-header">
        <div>
          <h4>Crew-Notiz</h4>
          <p class="muted">Optional für konkrete Begründung, Alternativen oder Feintuning.</p>
        </div>
        <select class="select preset-select" @change="appendOption($event, 'crew_setup')">
          <option value="">Crew-Fokus hinzufügen</option>
          <option v-for="option in optionsFor('crew_focus')" :key="option.id" :value="optionLabel(option)">{{ optionLabel(option) }}</option>
        </select>
      </div>
      <textarea v-model.trim="form.crew_setup" class="textarea compact-textarea" placeholder="Warum diese Verteilung? Welche Crew zuerst ersetzen/priorisieren?" />
    </section>

    <div class="build-designer-grid">
      <section class="setup-section designer-panel">
        <div class="setup-section-header">
          <div>
            <h3>Munition / Payloads</h3>
            <p class="muted">Standardmunition, Spezialmunition, Minen und Barrels.</p>
          </div>
          <select class="select preset-select" @change="appendOption($event, 'ammunition_setup')">
            <option value="">Munition hinzufügen</option>
            <option v-for="option in optionsFor('ammunition')" :key="option.id" :value="optionLabel(option)">{{ optionLabel(option) }}</option>
          </select>
        </div>
        <textarea v-model.trim="form.ammunition_setup" class="textarea" placeholder="Round Shots, Bar Shots, Grapeshot, Phosphorous ..." />
      </section>

      <section class="setup-section designer-panel">
        <div class="setup-section-header">
          <div>
            <h3>Verbrauchsgüter</h3>
            <p class="muted">Reparaturen, Smoke, Powder, Rations und Utility.</p>
          </div>
          <select class="select preset-select" @change="appendOption($event, 'consumable_setup')">
            <option value="">Verbrauchsgut hinzufügen</option>
            <option v-for="option in optionsFor('consumable')" :key="option.id" :value="optionLabel(option)">{{ optionLabel(option) }}</option>
          </select>
        </div>
        <textarea v-model.trim="form.consumable_setup" class="textarea" placeholder="Iron Patches, Smoke Bomb, Rum Ration ..." />
      </section>
    </div>

    <section class="setup-section designer-panel">
      <div class="setup-section-header">
        <div>
          <h3>Ladung / Hold</h3>
          <p class="muted">Reparaturmaterial, Handelswaren, Crafting-Mats und Vorräte.</p>
        </div>
        <select class="select preset-select" @change="appendOption($event, 'cargo_setup')">
          <option value="">Ladung hinzufügen</option>
          <option v-for="option in optionsFor('cargo')" :key="option.id" :value="optionLabel(option)">{{ optionLabel(option) }}</option>
        </select>
      </div>
      <textarea v-model.trim="form.cargo_setup" class="textarea" placeholder="Reparaturmaterial, Wood, Iron, Canvas, Handelswaren ..." />
    </section>

    <section class="setup-section designer-panel">
      <div class="setup-section-header">
        <div>
          <h3>Spielweise / Taktik</h3>
          <p class="muted">Wie wird das Build gefahren?</p>
        </div>
        <select class="select preset-select" @change="appendPreset($event, 'tactics')">
          <option value="">Baustein hinzufügen</option>
          <option v-for="preset in tacticsPresetOptions" :key="preset" :value="preset">{{ preset }}</option>
        </select>
      </div>
      <textarea v-model.trim="form.tactics" class="textarea" placeholder="Stärken, Schwächen, Gruppenspiel, Abbruchkriterien ..." />
    </section>

    <div class="form-row">
      <label for="buildNotes">Weitere Notizen</label>
      <textarea id="buildNotes" v-model.trim="form.notes" class="textarea" maxlength="4000" />
    </div>

    <div class="actions compact-actions">
      <button class="button" type="submit">Build speichern</button>
      <button class="button secondary" type="button" @click="handleCancel">Abbrechen</button>
    </div>
  </form>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'

import {
  buildPurposeOptions,
  buildRoleOptions,
  shipClassOptions,
  tacticsPresetOptions,
} from '@/constants/wosbOptions'

const props = defineProps({
  ships: {
    type: Array,
    default: () => [],
  },
  buildOptions: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['submit', 'cancel'])

const initialForm = {
  title: '',
  ship_id: null,
  ship_class: 'Beliebig',
  purpose: 'Allround',
  build_role: '',
  cannon_setup: '',
  weapon_bow_setup: '',
  weapon_port_setup: '',
  weapon_starboard_setup: '',
  weapon_stern_setup: '',
  sail_setup: '',
  upgrade_setup: '',
  crew_target: null,
  crew_gunnery: 0,
  crew_sailing: 0,
  crew_repair: 0,
  crew_boarding: 0,
  crew_setup: '',
  special_crew_setup: '',
  cargo_setup: '',
  ammunition_setup: '',
  consumable_setup: '',
  tactics: '',
  notes: '',
}

const form = reactive({ ...initialForm })
const shipSelection = ref('')
const selectedShip = computed(() => props.ships.find((ship) => String(ship.id) === shipSelection.value) || null)
const selectedShipRate = computed(() => parseRate(selectedShip.value?.rate))
const crewSliderMax = computed(() => Number(form.crew_target || selectedShip.value?.crew || 500))
const crewTotal = computed(
  () => Number(form.crew_gunnery || 0) + Number(form.crew_sailing || 0) + Number(form.crew_repair || 0) + Number(form.crew_boarding || 0),
)
const crewDelta = computed(() => Number(form.crew_target || 0) - crewTotal.value)
const crewDeltaClass = computed(() => {
  if (!form.crew_target) {
    return 'neutral'
  }
  if (crewDelta.value === 0) {
    return 'ok'
  }
  return crewDelta.value > 0 ? 'under' : 'over'
})
const crewBalanceText = computed(() => {
  if (!form.crew_target) {
    return `Verteilt: ${crewTotal.value}`
  }
  if (crewDelta.value === 0) {
    return `Perfekt verteilt: ${crewTotal.value}/${form.crew_target}`
  }
  if (crewDelta.value > 0) {
    return `Noch frei: ${crewDelta.value} · verteilt ${crewTotal.value}/${form.crew_target}`
  }
  return `Über Limit: ${Math.abs(crewDelta.value)} · verteilt ${crewTotal.value}/${form.crew_target}`
})

const weaponPositions = [
  {
    field: 'weapon_bow_setup',
    label: 'Bug',
    hint: 'Chaser / Anfahrt',
    placeholder: 'z. B. 4x Long Cannons für Chase und Eröffnung ...',
  },
  {
    field: 'weapon_port_setup',
    label: 'Backbord',
    hint: 'linke Breitseite',
    placeholder: 'z. B. 24x Standard Cannons als Hauptbreitseite ...',
  },
  {
    field: 'weapon_starboard_setup',
    label: 'Steuerbord',
    hint: 'rechte Breitseite',
    placeholder: 'z. B. gleich wie Backbord oder alternative Munition ...',
  },
  {
    field: 'weapon_stern_setup',
    label: 'Heck',
    hint: 'Rückzug / Kiten',
    placeholder: 'z. B. 2x Long Cannons oder leichte Chaser für Rückzug ...',
  },
]

const crewCategories = [
  { key: 'crew_gunnery', label: 'Kanoniere', hint: 'Reload, Feuerdruck, Waffenbedienung' },
  { key: 'crew_sailing', label: 'Segel', hint: 'Handling, Positionierung, Rückzug' },
  { key: 'crew_repair', label: 'Reparatur', hint: 'Sustain, Brand/Lecks, Durchhalten' },
  { key: 'crew_boarding', label: 'Boarding', hint: 'Enterkampf, Nahkampf, Crew-Druck' },
]

const upgradeSlots = reactive([
  { label: 'Slot 1 · Basis', category: 'upgrade', value: '' },
  { label: 'Slot 2 · Basis', category: 'upgrade', value: '' },
  { label: 'Slot 3 · XP', category: 'upgrade', value: '' },
  { label: 'Slot 4 · XP', category: 'upgrade', value: '' },
  { label: 'Spezialslot · später', category: 'special_upgrade', value: '' },
])

watch(shipSelection, (selection) => {
  if (!selection) {
    form.ship_id = null
    form.crew_target = null
    distributeCrew({ gunnery: 0, sailing: 0, repair: 0, boarding: 0 })
    return
  }

  const ship = selectedShip.value
  form.ship_id = ship ? ship.id : null
  if (ship?.ship_class) {
    form.ship_class = ship.ship_class
  }
  if (ship?.crew) {
    form.crew_target = ship.crew
    applyDistributionByPurpose()
  }
})

function resetForm() {
  Object.assign(form, initialForm)
  shipSelection.value = ''
  upgradeSlots.forEach((slot) => {
    slot.value = ''
  })
}

function submitForm() {
  const payload = {
    ...form,
    ship_id: form.ship_id || null,
    ship_class: form.ship_class || 'Beliebig',
    build_role: form.build_role || null,
    crew_target: form.crew_target || null,
    crew_gunnery: normalizeNullableNumber(form.crew_gunnery),
    crew_sailing: normalizeNullableNumber(form.crew_sailing),
    crew_repair: normalizeNullableNumber(form.crew_repair),
    crew_boarding: normalizeNullableNumber(form.crew_boarding),
  }
  emit('submit', payload)
  resetForm()
}

function normalizeNullableNumber(value) {
  const parsed = Number(value || 0)
  return parsed > 0 ? parsed : null
}

function handleCancel() {
  resetForm()
  emit('cancel')
}

function fillMaxCrew() {
  if (selectedShip.value?.crew) {
    form.crew_target = selectedShip.value.crew
    applyDistributionByPurpose()
  }
}

function normalizeCrewAfterTargetChange() {
  if (!form.crew_target) {
    return
  }
  const target = Number(form.crew_target)
  crewCategories.forEach((category) => {
    if (Number(form[category.key] || 0) > target) {
      form[category.key] = target
    }
  })
}

function clampCrew(key) {
  const max = crewSliderMax.value
  const value = Number(form[key] || 0)
  if (value < 0) {
    form[key] = 0
  }
  if (value > max) {
    form[key] = max
  }
}

function applyCrewPreset(event) {
  const preset = event.target.value
  event.target.value = ''
  if (!preset) {
    return
  }
  const presets = {
    balanced: { gunnery: 30, sailing: 25, repair: 25, boarding: 20 },
    gunnery: { gunnery: 45, sailing: 20, repair: 25, boarding: 10 },
    sailing: { gunnery: 25, sailing: 40, repair: 25, boarding: 10 },
    repair: { gunnery: 25, sailing: 20, repair: 45, boarding: 10 },
    boarding: { gunnery: 25, sailing: 15, repair: 20, boarding: 40 },
  }
  distributeCrew(presets[preset])
}

function applyDistributionByPurpose() {
  const role = String(form.build_role || form.purpose || '').toLowerCase()
  if (role.includes('scout') || role.includes('aufklärung')) {
    distributeCrew({ gunnery: 25, sailing: 40, repair: 25, boarding: 10 })
    return
  }
  if (role.includes('boarding')) {
    distributeCrew({ gunnery: 25, sailing: 15, repair: 20, boarding: 40 })
    return
  }
  if (role.includes('tank') || role.includes('linie')) {
    distributeCrew({ gunnery: 35, sailing: 15, repair: 35, boarding: 15 })
    return
  }
  distributeCrew({ gunnery: 35, sailing: 20, repair: 30, boarding: 15 })
}

function distributeCrew(weights) {
  const target = Number(form.crew_target || selectedShip.value?.crew || 0)
  if (!target) {
    form.crew_gunnery = 0
    form.crew_sailing = 0
    form.crew_repair = 0
    form.crew_boarding = 0
    return
  }

  const gunnery = Math.floor((target * Number(weights.gunnery || 0)) / 100)
  const sailing = Math.floor((target * Number(weights.sailing || 0)) / 100)
  const repair = Math.floor((target * Number(weights.repair || 0)) / 100)
  const boarding = Math.max(0, target - gunnery - sailing - repair)
  form.crew_gunnery = gunnery
  form.crew_sailing = sailing
  form.crew_repair = repair
  form.crew_boarding = boarding
}

function applyUpgradeSlots() {
  const lines = upgradeSlots
    .filter((slot) => slot.value)
    .map((slot) => `${slot.label}: ${slot.value}`)
  if (!lines.length) {
    return
  }
  const block = lines.map((line) => `- ${line}`).join('\n')
  form.upgrade_setup = form.upgrade_setup ? `${form.upgrade_setup}\n${block}` : block
}

function setWeaponPosition(event, fieldName, label) {
  const value = event.target.value
  event.target.value = ''
  if (!value) {
    return
  }
  const line = `${label}: ${value}`
  form[fieldName] = form[fieldName] ? `${form[fieldName]}\n- ${line}` : `- ${line}`
}

function appendOption(event, fieldName) {
  appendValue(event.target.value, fieldName)
  event.target.value = ''
}

function appendPreset(event, fieldName) {
  appendValue(event.target.value, fieldName)
  event.target.value = ''
}

function appendValue(value, fieldName) {
  if (!value) {
    return
  }
  form[fieldName] = form[fieldName] ? `${form[fieldName]}\n- ${value}` : `- ${value}`
}

function optionsFor(category) {
  return props.buildOptions.filter((option) => option.category === category && optionMatchesShip(option))
}

function optionMatchesShip(option) {
  const ship = selectedShip.value
  if (!ship) {
    return true
  }
  const rate = selectedShipRate.value
  if (option.min_rate && rate && rate < option.min_rate) {
    return false
  }
  if (option.max_rate && rate && rate > option.max_rate) {
    return false
  }
  if (option.progression_class && option.progression_class !== ship.progression_class) {
    return false
  }
  if (option.ship_class && option.ship_class !== ship.ship_class) {
    return false
  }
  return true
}

function optionLabel(option) {
  const parts = [option.name]
  if (option.effect_hint) {
    parts.push(option.effect_hint)
  }
  if (option.description) {
    parts.push(option.description)
  }
  return parts.join(' · ')
}

function shipOptionLabel(ship) {
  const crewLabel = ship.crew ? `Crew ${ship.crew}` : 'Crew —'
  return `${ship.name} · ${ship.progression_class} · ${ship.ship_class} · ${crewLabel}`
}

function parseRate(rate) {
  if (rate === null || rate === undefined) {
    return null
  }

  const normalized = String(rate).trim().toUpperCase()
  const romanRates = {
    I: 1,
    II: 2,
    III: 3,
    IV: 4,
    V: 5,
    VI: 6,
    VII: 7,
  }
  if (romanRates[normalized]) {
    return romanRates[normalized]
  }

  const parsed = Number.parseInt(normalized.replace(/[^0-9]/g, ''), 10)
  return Number.isNaN(parsed) ? null : parsed
}
</script>
