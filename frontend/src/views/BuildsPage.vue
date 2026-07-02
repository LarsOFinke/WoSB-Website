<template>
  <section class="management-flow">
    <div class="card management-list-card">
      <div class="section-heading">
        <span class="badge">Schiffs-Builds</span>
        <h1>Builds</h1>
        <p class="muted">
          Öffentliche Sammlung echter Ingame-Schiffs-Builds: Schiff, Rolle, Upgrades, Crew, Ladung, Munition,
          Verbrauchsgüter und Spielweise. Gäste dürfen Builds lesen; neue Builds können nur angemeldete Benutzer anlegen.
        </p>
      </div>

      <div class="page-info-panel page-info-panel-top">
        <h2>Nächste Schritte</h2>
        <p class="muted">
          Öffne ein Build für Details und nutze die Setups als Vorlage im Spiel. Wenn du eigene Builds dokumentieren
          möchtest, melde dich an und nutze das strukturierte Overlay mit Schiffsauswahl, Rollen- und Setup-Dropdowns.
        </p>
        <div class="actions compact-actions">
          <button v-if="isAuthenticated" class="button" type="button" @click="showCreateOverlay = true">
            Neuen Build anlegen
          </button>
          <RouterLink v-else class="button" to="/login">Anmelden zum Erstellen</RouterLink>
          <RouterLink v-if="!isAuthenticated" class="button secondary" to="/register">Registrieren</RouterLink>
        </div>
      </div>

      <MessageBox :message="message" />

      <div class="list-section-header">
        <div>
          <h2>Gespeicherte Schiffs-Builds</h2>
          <p class="muted">Alle öffentlichen Build-Vorschläge mit Schiff, Setup, Rolle und Einsatzzweck.</p>
        </div>
        <span class="badge">{{ builds.length }} Builds</span>
      </div>

      <div class="list">
        <BuildCard v-for="build in builds" :key="build.id" :build="build" @select="selectBuild" />
      </div>
    </div>

    <BuildFormOverlay
      :open="showCreateOverlay"
      :ships="ships"
      :build-options="buildOptions"
      @submit="createBuild"
      @close="showCreateOverlay = false"
    />

    <DetailOverlay :open="Boolean(selectedBuild)" :title="selectedBuild?.title || ''" :eyebrow="selectedBuild?.purpose || ''" @close="selectedBuild = null">
      <template v-if="selectedBuild">
        <div class="detail-grid">
          <div><strong>Schiff</strong><span>{{ selectedBuild.ship_name || selectedBuild.ship_class }}</span></div>
          <div><strong>Rate</strong><span>{{ formatRate(selectedBuild.rate) }}</span></div>
          <div><strong>Einsatzbereich</strong><span>{{ selectedBuild.purpose || 'Allround' }}</span></div>
          <div><strong>Build-Rolle</strong><span>{{ selectedBuild.build_role || 'Keine feste Rolle' }}</span></div>
          <div><strong>Crew-Ziel</strong><span>{{ selectedBuild.crew_target ? `${selectedBuild.crew_target} / ${selectedBuild.ship_crew || '?'}` : selectedBuild.ship_crew || '—' }}</span></div>
          <div><strong>Verteilte Crew</strong><span>{{ crewDistributionTotal(selectedBuild) || '—' }}</span></div>
          <div><strong>Autor</strong><span>{{ selectedBuild.author_name || `#${selectedBuild.author_id}` }}</span></div>
        </div>

        <div class="build-detail-sections">
          <section>
            <h3>Bewaffnung nach Position</h3>
            <div class="weapon-detail-grid">
              <div><strong>Bug</strong><p class="muted preserve-lines">{{ selectedBuild.weapon_bow_setup || '—' }}</p></div>
              <div><strong>Backbord</strong><p class="muted preserve-lines">{{ selectedBuild.weapon_port_setup || '—' }}</p></div>
              <div><strong>Steuerbord</strong><p class="muted preserve-lines">{{ selectedBuild.weapon_starboard_setup || '—' }}</p></div>
              <div><strong>Heck</strong><p class="muted preserve-lines">{{ selectedBuild.weapon_stern_setup || '—' }}</p></div>
            </div>
            <p class="muted preserve-lines">{{ selectedBuild.cannon_setup || 'Keine allgemeine Waffen-Notiz hinterlegt.' }}</p>
          </section>
          <section>
            <h3>Segel-Slot</h3>
            <p class="muted preserve-lines">{{ selectedBuild.sail_setup || 'Kein Segel-Setup hinterlegt.' }}</p>
          </section>
          <section>
            <h3>Upgrades / Module</h3>
            <p class="muted preserve-lines">{{ selectedBuild.upgrade_setup || 'Keine Upgrades hinterlegt.' }}</p>
          </section>
          <section>
            <h3>Crew-Verteilung</h3>
            <div class="crew-detail-bars">
              <div v-for="category in crewCategories" :key="category.key" class="crew-detail-row">
                <span>{{ category.label }}</span>
                <div class="crew-detail-track"><i :style="{ width: crewBarWidth(selectedBuild, category.key) }"></i></div>
                <strong>{{ selectedBuild[category.key] || 0 }}</strong>
              </div>
            </div>
            <p class="muted preserve-lines">{{ selectedBuild.crew_setup || 'Keine zusätzliche Crew-Notiz hinterlegt.' }}</p>
          </section>
          <section>
            <h3>Spezialcrew</h3>
            <p class="muted preserve-lines">{{ selectedBuild.special_crew_setup || 'Keine Spezialcrew hinterlegt.' }}</p>
          </section>
          <section>
            <h3>Ladung</h3>
            <p class="muted preserve-lines">{{ selectedBuild.cargo_setup || 'Keine Ladung hinterlegt.' }}</p>
          </section>
          <section>
            <h3>Munition</h3>
            <p class="muted preserve-lines">{{ selectedBuild.ammunition_setup || 'Keine Munition hinterlegt.' }}</p>
          </section>
          <section>
            <h3>Verbrauchsgüter</h3>
            <p class="muted preserve-lines">{{ selectedBuild.consumable_setup || 'Keine Verbrauchsgüter hinterlegt.' }}</p>
          </section>
          <section>
            <h3>Spielweise / Taktik</h3>
            <p class="muted preserve-lines">{{ selectedBuild.tactics || 'Keine Taktik hinterlegt.' }}</p>
          </section>
          <section>
            <h3>Weitere Notizen</h3>
            <p class="muted preserve-lines">{{ selectedBuild.notes || 'Keine weiteren Notizen vorhanden.' }}</p>
          </section>
        </div>
      </template>
    </DetailOverlay>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'

import BuildCard from '@/components/builds/BuildCard.vue'
import BuildFormOverlay from '@/components/builds/BuildFormOverlay.vue'
import DetailOverlay from '@/components/ui/DetailOverlay.vue'
import MessageBox from '@/components/ui/MessageBox.vue'
import { useSession } from '@/composables/useSession'
import { buildService } from '@/services/buildService'
import { shipService } from '@/services/shipService'

const { isAuthenticated } = useSession()

const message = ref('')
const builds = ref([])
const ships = ref([])
const buildOptions = ref([])
const selectedBuild = ref(null)
const showCreateOverlay = ref(false)

const crewCategories = [
  { key: 'crew_gunnery', label: 'Kanoniere' },
  { key: 'crew_sailing', label: 'Segel' },
  { key: 'crew_repair', label: 'Reparatur' },
  { key: 'crew_boarding', label: 'Boarding' },
]

async function loadBuilds() {
  try {
    builds.value = await buildService.list()
  } catch (error) {
    message.value = error.response?.data?.detail || 'Builds konnten nicht geladen werden.'
  }
}

async function loadShips() {
  try {
    ships.value = await shipService.list()
  } catch {
    ships.value = []
  }
}

async function loadBuildOptions() {
  try {
    buildOptions.value = await buildService.listOptions()
  } catch {
    buildOptions.value = []
  }
}

function selectBuild(build) {
  selectedBuild.value = build
}

async function createBuild(payload) {
  try {
    const created = await buildService.create(payload)
    builds.value = [created, ...builds.value]
    selectedBuild.value = created
    showCreateOverlay.value = false
    message.value = 'Build wurde gespeichert.'
  } catch (error) {
    message.value = error.response?.data?.detail || 'Build konnte nicht gespeichert werden.'
  }
}

function formatRate(rate) {
  if (!rate) {
    return '—'
  }
  const parsed = parseRate(rate)
  return parsed ? `Rate ${parsed}` : `Rate ${rate}`
}

function crewDistributionTotal(build) {
  return crewCategories.reduce((sum, category) => sum + Number(build?.[category.key] || 0), 0)
}

function crewBarWidth(build, key) {
  const target = Number(build?.crew_target || crewDistributionTotal(build) || 0)
  if (!target) {
    return '0%'
  }
  const value = Number(build?.[key] || 0)
  return `${Math.min(100, Math.round((value / target) * 100))}%`
}

function parseRate(rate) {
  const normalized = String(rate).trim().toUpperCase()
  const romanRates = { I: 1, II: 2, III: 3, IV: 4, V: 5, VI: 6, VII: 7 }
  if (romanRates[normalized]) {
    return romanRates[normalized]
  }
  const parsed = Number.parseInt(normalized.replace(/[^0-9]/g, ''), 10)
  return Number.isNaN(parsed) ? null : parsed
}

onMounted(async () => {
  await Promise.all([loadBuilds(), loadShips(), loadBuildOptions()])
})
</script>
