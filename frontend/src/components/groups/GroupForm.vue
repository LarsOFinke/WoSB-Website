<template>
  <form class="card" @submit.prevent="submitForm">
    <h2>Gruppe anlegen</h2>
    <p class="muted">Gruppen laufen automatisch nach 24 Stunden ab. Bevorzugte Schiffe sind Hinweise; harte Pflicht ist nur die Mindest-Rate.</p>

    <div class="form-row">
      <label for="title">Titel</label>
      <input id="title" v-model.trim="form.title" class="input" type="text" required maxlength="100" />
    </div>

    <div class="form-row">
      <label for="focus">Fokus</label>
      <select id="focus" v-model="form.focus" class="select">
        <option v-for="focus in focusOptions" :key="focus.value" :value="focus.value">{{ focus.label }}</option>
      </select>
    </div>

    <div class="form-row">
      <label for="shipId">Bevorzugtes Schiff</label>
      <select id="shipId" v-model.number="form.ship_id" class="select">
        <option :value="null">Beliebig</option>
        <option v-for="ship in ships" :key="ship.id" :value="ship.id">
          {{ ship.name }} · Rate {{ ship.rate }} · {{ ship.ship_class }}
        </option>
      </select>
    </div>

    <div class="grid grid-2 compact-form-grid">
      <div class="form-row">
        <label for="maxMembers">Maximale Teilnehmer</label>
        <input id="maxMembers" v-model.number="form.max_members" class="input" type="number" min="2" max="50" />
      </div>

      <div class="form-row">
        <label for="minShipRate">Mindest-Rate</label>
        <select id="minShipRate" v-model="form.min_ship_rate" class="select">
          <option :value="null">Keine</option>
          <option v-for="rate in rateOptions" :key="rate" :value="rate">Rate {{ rate }} oder besser</option>
        </select>
      </div>
    </div>

    <div class="form-row">
      <label for="fleetRestriction">Flottenhinweis / Beschränkung</label>
      <input id="fleetRestriction" v-model.trim="form.fleet_restriction" class="input" type="text" maxlength="120" placeholder="z. B. WoSB, Freunde, keine Beschränkung" />
    </div>

    <div class="form-row checkbox-row">
      <label>
        <input v-model="form.allow_anonymous" type="checkbox" />
        Gäste dürfen anonym beitreten
      </label>
    </div>

    <div class="form-row">
      <label for="scheduledAt">Geplanter Termin</label>
      <input id="scheduledAt" v-model="form.scheduled_at" class="input" type="datetime-local" />
    </div>

    <div class="form-row">
      <label for="description">Beschreibung / Anforderungen</label>
      <textarea id="description" v-model.trim="form.description" class="textarea" maxlength="2000" placeholder="Was wird gefahren? Welche Rollen, Schiffe oder Vorbereitung sind sinnvoll?" />
    </div>

    <button class="button" type="submit">Speichern</button>
  </form>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import { focusOptions, rateOptions } from '@/constants/wosbOptions'
import { shipService } from '@/services/shipService'

const emit = defineEmits(['submit'])
const ships = ref([])

const form = reactive({
  title: '',
  description: '',
  focus: 'pve_general',
  ship_id: null,
  ship_class: 'Beliebig',
  max_members: 8,
  min_ship_rate: null,
  allow_anonymous: true,
  fleet_restriction: '',
  scheduled_at: '',
})

function toApiDate(value) {
  return value ? new Date(value).toISOString() : null
}

function submitForm() {
  emit('submit', {
    ...form,
    fleet_restriction: form.fleet_restriction || null,
    scheduled_at: toApiDate(form.scheduled_at),
  })
  form.title = ''
  form.description = ''
  form.focus = 'pve_general'
  form.ship_id = null
  form.ship_class = 'Beliebig'
  form.max_members = 8
  form.min_ship_rate = null
  form.allow_anonymous = true
  form.fleet_restriction = ''
  form.scheduled_at = ''
}

onMounted(async () => {
  try {
    ships.value = await shipService.list()
  } catch {
    ships.value = []
  }
})
</script>
