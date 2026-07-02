<template>
  <article class="list-item clickable build-list-item" tabindex="0" @click="$emit('select', build)" @keydown.enter="$emit('select', build)">
    <div class="list-item-header">
      <div>
        <div class="badge-row">
          <span class="badge">{{ build.purpose || 'Allround' }}</span>
          <span v-if="build.build_role" class="badge subtle-badge">{{ build.build_role }}</span>
          <span v-if="build.can_manage" class="badge">Dein Build</span>
        </div>
        <h3>{{ build.title }}</h3>
      </div>
      <button class="button small secondary" type="button" @click.stop="$emit('select', build)">Details</button>
    </div>

    <p class="muted build-card-ship-line">{{ build.ship_name || build.ship_class || 'Kein Schiff gewählt' }}</p>

    <div class="quick-fact-grid">
      <span v-if="build.rate" class="quick-fact"><strong>{{ formatRate(build.rate) }}</strong><small>Rate</small></span>
      <span v-if="build.ship_class" class="quick-fact"><strong>{{ build.ship_class }}</strong><small>Klasse</small></span>
      <span v-if="crewSummary" class="quick-fact"><strong>{{ crewSummary }}</strong><small>Crew</small></span>
      <span v-if="weaponSummary" class="quick-fact"><strong>{{ weaponSummary }}</strong><small>Bewaffnung</small></span>
    </div>

    <div class="build-card-preview-grid">
      <p v-if="weaponPreview" class="muted preserve-lines"><strong>Waffen:</strong> {{ weaponPreview }}</p>
      <p v-if="upgradePreview" class="muted preserve-lines"><strong>Upgrades:</strong> {{ upgradePreview }}</p>
      <p v-if="setupPreview" class="muted preserve-lines"><strong>Setup:</strong> {{ setupPreview }}</p>
    </div>

    <p class="muted build-card-author">Autor: {{ build.author_name || `#${build.author_id}` }}</p>
  </article>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  build: {
    type: Object,
    required: true,
  },
})

function firstFilled(...values) {
  return values.find((value) => typeof value === 'string' && value.trim().length > 0)
}

function shorten(value, maxLength = 160) {
  if (!value) {
    return ''
  }
  const compact = String(value).replace(/\s+/g, ' ').trim()
  return compact.length > maxLength ? `${compact.slice(0, maxLength)}…` : compact
}

function countFilled(...values) {
  return values.filter((value) => typeof value === 'string' && value.trim().length > 0).length
}

function formatRate(rate) {
  const parsed = parseRate(rate)
  return parsed ? `${parsed}` : `${rate}`
}

function parseRate(rate) {
  if (rate === null || rate === undefined) {
    return null
  }
  const normalized = String(rate).trim().toUpperCase()
  const romanRates = { I: 1, II: 2, III: 3, IV: 4, V: 5, VI: 6, VII: 7 }
  if (romanRates[normalized]) {
    return romanRates[normalized]
  }
  const parsed = Number.parseInt(normalized.replace(/[^0-9]/g, ''), 10)
  return Number.isNaN(parsed) ? null : parsed
}

const crewSummary = computed(() => {
  const distribution = [props.build.crew_gunnery, props.build.crew_sailing, props.build.crew_repair, props.build.crew_boarding]
    .map((value) => Number(value || 0))
    .reduce((sum, value) => sum + value, 0)

  if (props.build.crew_target && distribution) {
    return `${distribution}/${props.build.crew_target}`
  }
  if (props.build.crew_target) {
    return `${props.build.crew_target}`
  }
  if (props.build.ship_crew) {
    return `max ${props.build.ship_crew}`
  }
  return ''
})

const weaponSummary = computed(() => {
  const filled = countFilled(
    props.build.weapon_bow_setup,
    props.build.weapon_port_setup,
    props.build.weapon_starboard_setup,
    props.build.weapon_stern_setup,
  )
  if (!filled) {
    return ''
  }
  return `${filled}/4 Positionen`
})

const weaponPreview = computed(() =>
  shorten(
    firstFilled(
      props.build.weapon_port_setup && `Backbord ${props.build.weapon_port_setup}`,
      props.build.weapon_starboard_setup && `Steuerbord ${props.build.weapon_starboard_setup}`,
      props.build.weapon_bow_setup && `Bug ${props.build.weapon_bow_setup}`,
      props.build.weapon_stern_setup && `Heck ${props.build.weapon_stern_setup}`,
      props.build.cannon_setup,
    ),
    180,
  ),
)

const upgradePreview = computed(() => shorten(props.build.upgrade_setup, 150))
const setupPreview = computed(() =>
  shorten(
    firstFilled(
      props.build.sail_setup,
      props.build.crew_setup,
      props.build.ammunition_setup,
      props.build.consumable_setup,
      props.build.cargo_setup,
      props.build.notes,
    ),
    150,
  ),
)
</script>
