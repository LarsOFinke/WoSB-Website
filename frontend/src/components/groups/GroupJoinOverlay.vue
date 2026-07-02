<template>
  <DetailOverlay :open="open" :title="title" :eyebrow="eyebrow" @close="handleClose">
    <form v-if="group" class="join-form" @submit.prevent="submitJoin">
      <p class="muted">
        Melde dich für diese Gruppe an. Wähle nach Möglichkeit ein Schiff aus dem Katalog aus; die Rate wird dann
        automatisch erkannt. Bei freien Schiffen wählst du die Rate manuell.
      </p>

      <div class="join-group-summary">
        <span><strong>Freie Plätze:</strong> {{ group.free_slots }} von {{ group.max_members }}</span>
        <span><strong>Mindest-Rate:</strong> {{ minRateLabel }}</span>
        <span><strong>Anonymer Beitritt:</strong> {{ group.allow_anonymous ? 'Erlaubt' : 'Nicht erlaubt' }}</span>
        <span v-if="group.fleet_restriction"><strong>Flottenhinweis:</strong> {{ group.fleet_restriction }}</span>
      </div>

      <div v-if="!isAuthenticated" class="form-row">
        <label for="join-display-name">Ingame-Name *</label>
        <input id="join-display-name" v-model.trim="form.display_name" class="input" type="text" maxlength="80" required placeholder="z. B. Captain Nelson" />
      </div>

      <div v-else class="form-row">
        <label for="join-display-name">Anzeigename überschreiben optional</label>
        <input id="join-display-name" v-model.trim="form.display_name" class="input" type="text" maxlength="80" placeholder="Leer lassen für deinen Profilnamen" />
      </div>

      <div class="grid grid-2 compact-form-grid">
        <div class="form-row">
          <label for="join-fleet">Flotte optional</label>
          <input id="join-fleet" v-model.trim="form.fleet_name" class="input" type="text" maxlength="120" placeholder="z. B. WoSB Flotte" />
        </div>

        <div class="form-row">
          <label for="join-role">Rolle optional</label>
          <select id="join-role" class="select" v-model="form.participant_role">
            <option value="">Keine feste Rolle</option>
            <option v-for="role in roleOptions" :key="role" :value="role">{{ role }}</option>
          </select>
        </div>
      </div>

      <div class="grid grid-2 compact-form-grid">
        <div class="form-row">
          <label for="join-ship">Schiff</label>
          <select id="join-ship" class="select" v-model="shipSelection">
            <option value="">Noch kein Schiff festlegen</option>
            <option value="custom">Anderes Schiff frei eintragen</option>
            <option v-for="ship in ships" :key="ship.id" :value="String(ship.id)" :disabled="!isShipAllowed(ship)">
              {{ shipOptionLabel(ship) }}
            </option>
          </select>
          <small v-if="minRate" class="muted">
            Schiffe unterhalb der Mindestanforderung bleiben sichtbar, sind aber ausgegraut.
          </small>
        </div>

        <div class="form-row">
          <label for="join-detected-rate">Erkannte Rate</label>
          <input id="join-detected-rate" class="input" type="text" :value="detectedRateLabel" readonly />
        </div>
      </div>

      <div v-if="shipSelection === 'custom'" class="grid grid-2 compact-form-grid">
        <div class="form-row">
          <label for="join-custom-ship">Freies Schiff</label>
          <input id="join-custom-ship" v-model.trim="form.custom_ship_name" class="input" type="text" maxlength="120" placeholder="Schiffsname" />
        </div>

        <div class="form-row">
          <label for="join-custom-rate">Schiffsrate</label>
          <select id="join-custom-rate" class="select" v-model="form.custom_ship_rate" :required="requiresRate">
            <option value="">Bitte auswählen</option>
            <option v-for="rate in rateOptions" :key="rate" :value="rate" :disabled="!isRateAllowed(rate)">
              {{ rateOptionLabel(rate) }}
            </option>
          </select>
        </div>
      </div>

      <div v-else-if="requiresRate && !shipSelection" class="form-row">
        <label for="join-rate-only">Schiffsrate *</label>
        <select id="join-rate-only" class="select" v-model="form.custom_ship_rate" required>
          <option value="">Bitte auswählen</option>
          <option v-for="rate in rateOptions" :key="rate" :value="rate" :disabled="!isRateAllowed(rate)">
            {{ rateOptionLabel(rate) }}
          </option>
        </select>
      </div>

      <div class="form-row">
        <label for="join-note">Notiz optional</label>
        <textarea id="join-note" class="textarea" v-model.trim="form.note" maxlength="1000" rows="4" placeholder="z. B. Voice vorhanden, bevorzugte Rolle, Zeitraum ..." />
      </div>

      <MessageBox :message="localMessage" />

      <div class="actions">
        <button class="button" type="submit" :disabled="submitting">
          {{ submitting ? 'Melde an ...' : 'Zur Gruppe anmelden' }}
        </button>
        <button class="button secondary" type="button" @click="handleClose">Abbrechen</button>
      </div>
    </form>
  </DetailOverlay>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'

import { participantRoleOptions, rateOptions } from '@/constants/wosbOptions'
import DetailOverlay from '@/components/ui/DetailOverlay.vue'
import MessageBox from '@/components/ui/MessageBox.vue'

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  group: {
    type: Object,
    default: null,
  },
  ships: {
    type: Array,
    default: () => [],
  },
  isAuthenticated: {
    type: Boolean,
    default: false,
  },
  submitting: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'submit'])

const roleOptions = participantRoleOptions

const shipSelection = ref('')
const localMessage = ref('')
const form = reactive({
  display_name: '',
  fleet_name: '',
  participant_role: '',
  custom_ship_name: '',
  custom_ship_rate: '',
  note: '',
})

const title = computed(() => (props.group ? `Teilnahme: ${props.group.title}` : 'Teilnehmen'))
const eyebrow = computed(() => props.group?.focus_label || props.group?.focus || 'Gruppenbeitritt')
const minRate = computed(() => (props.group?.min_ship_rate ? Number(props.group.min_ship_rate) : null))
const requiresRate = computed(() => !props.isAuthenticated && Boolean(minRate.value))
const minRateLabel = computed(() => (minRate.value ? `Rate ${minRate.value} oder besser` : 'Keine Mindest-Rate'))

const selectedShip = computed(() => props.ships.find((ship) => String(ship.id) === shipSelection.value) || null)
const selectedShipRate = computed(() => parseRate(selectedShip.value?.rate))
const detectedRateLabel = computed(() => {
  if (selectedShip.value) {
    return selectedShipRate.value ? `${formatRate(selectedShip.value.rate)} aus dem Schiffskatalog` : 'Rate im Katalog unbekannt'
  }
  if (shipSelection.value === 'custom') {
    return form.custom_ship_rate ? `Rate ${form.custom_ship_rate} manuell` : 'Bitte manuell auswählen'
  }
  if (form.custom_ship_rate) {
    return `Rate ${form.custom_ship_rate} manuell`
  }
  return 'Noch keine Rate gewählt'
})

watch(
  () => props.open,
  (open) => {
    if (open) {
      resetForm()
    }
  },
)

watch(shipSelection, (selection) => {
  if (selection !== 'custom') {
    form.custom_ship_name = ''
  }
  if (selection && selection !== 'custom') {
    form.custom_ship_rate = selectedShipRate.value ? String(selectedShipRate.value) : ''
  } else {
    form.custom_ship_rate = ''
  }
})

function resetForm() {
  shipSelection.value = ''
  localMessage.value = ''
  form.display_name = ''
  form.fleet_name = ''
  form.participant_role = ''
  form.custom_ship_name = ''
  form.custom_ship_rate = ''
  form.note = ''

  const preferredShip = props.group?.ship_id ? props.ships.find((ship) => ship.id === props.group.ship_id) : null
  if (preferredShip && isShipAllowed(preferredShip)) {
    shipSelection.value = String(preferredShip.id)
    const rate = parseRate(preferredShip.rate)
    form.custom_ship_rate = rate ? String(rate) : ''
  }
}

function submitJoin() {
  localMessage.value = ''

  if (!props.isAuthenticated && !form.display_name.trim()) {
    localMessage.value = 'Bitte gib deinen Ingame-Namen an.'
    return
  }

  if (shipSelection.value && shipSelection.value !== 'custom' && !isShipAllowed(selectedShip.value)) {
    localMessage.value = 'Das ausgewählte Schiff erfüllt die Mindest-Rate nicht.'
    return
  }

  if (requiresRate.value && !shipSelection.value && !form.custom_ship_rate) {
    localMessage.value = 'Bitte wähle ein Schiff oder gib deine Schiffsrate an.'
    return
  }

  if (form.custom_ship_rate && !isRateAllowed(Number(form.custom_ship_rate))) {
    localMessage.value = 'Die ausgewählte Rate erfüllt die Mindest-Rate nicht.'
    return
  }

  const payload = {}
  addText(payload, 'display_name', form.display_name)
  addText(payload, 'fleet_name', form.fleet_name)
  addText(payload, 'participant_role', form.participant_role)
  addText(payload, 'note', form.note)

  if (shipSelection.value === 'custom') {
    addText(payload, 'custom_ship_name', form.custom_ship_name)
    addNumber(payload, 'custom_ship_rate', form.custom_ship_rate)
  } else if (shipSelection.value) {
    payload.ship_id = Number(shipSelection.value)
  } else {
    addNumber(payload, 'custom_ship_rate', form.custom_ship_rate)
  }

  emit('submit', payload)
}

function handleClose() {
  emit('close')
}

function addText(payload, key, value) {
  const normalized = value?.trim()
  if (normalized) {
    payload[key] = normalized
  }
}

function addNumber(payload, key, value) {
  if (value === '' || value === null || value === undefined) {
    return
  }
  const parsed = Number.parseInt(value, 10)
  if (!Number.isNaN(parsed)) {
    payload[key] = parsed
  }
}

function isRateAllowed(rate) {
  if (!minRate.value || !rate) {
    return true
  }
  return Number(rate) <= minRate.value
}

function isShipAllowed(ship) {
  if (!ship) {
    return true
  }
  const rate = parseRate(ship.rate)
  return rate !== null && isRateAllowed(rate)
}

function shipOptionLabel(ship) {
  const suffix = isShipAllowed(ship) ? '' : ' · nicht ausreichend'
  return `${ship.name} · ${formatRate(ship.rate)} · ${ship.ship_class}${suffix}`
}

function rateOptionLabel(rate) {
  return isRateAllowed(rate) ? `Rate ${rate}` : `Rate ${rate} · nicht ausreichend`
}

function formatRate(rate) {
  const parsed = parseRate(rate)
  return parsed ? `Rate ${parsed}` : `Rate ${rate}`
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
