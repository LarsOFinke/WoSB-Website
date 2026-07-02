<template>
  <section class="management-flow">
    <div class="card management-list-card">
      <div class="section-heading">
        <span class="badge">Gruppenübersicht</span>
        <h1>Gruppen</h1>
        <p class="muted">
          Öffentliche Übersicht aktiver Gruppen. Die Karten zeigen Fokus, Anforderungen, freie Plätze und Ablaufzeit.
          Gäste können offenen Gruppen anonym beitreten, sofern die Gruppe das erlaubt.
        </p>
      </div>

      <div class="page-info-panel page-info-panel-top">
        <h2>Nächste Schritte</h2>
        <p class="muted">
          Öffne eine Gruppe für Details, prüfe Mindest-Rate und Flottenhinweis und melde dich dann an. Gruppenleiter
          und Admins verwalten Gruppen weiterhin ausschließlich über geschützte Backend-Rechte.
        </p>
        <div class="actions compact-actions">
          <RouterLink v-if="isAuthenticated" class="button" to="/group-management">Eigene Gruppen verwalten</RouterLink>
          <RouterLink v-else class="button" to="/login">Anmelden zum Erstellen</RouterLink>
          <RouterLink v-if="!isAuthenticated" class="button secondary" to="/register">Registrieren</RouterLink>
        </div>
      </div>

      <MessageBox :message="message" />

      <div class="list-section-header">
        <div>
          <h2>Aktive Gruppen</h2>
          <p class="muted">Archivierte, geschlossene und abgelaufene Gruppen erscheinen nicht in dieser öffentlichen Liste.</p>
        </div>
        <span class="badge">{{ groups.length }} Gruppen</span>
      </div>

      <div class="list">
        <GroupCard v-for="group in groups" :key="group.id" :group="group" @select="selectGroup" @join="openJoinOverlay" />
      </div>
    </div>

    <DetailOverlay :open="Boolean(selectedGroup)" :title="selectedGroup?.title || ''" :eyebrow="selectedGroup?.focus_label || ''" @close="selectedGroup = null">
      <template v-if="selectedGroup">
        <p class="muted">{{ selectedGroup.description || 'Keine Beschreibung hinterlegt.' }}</p>
        <div class="detail-grid">
          <div><strong>Leitung</strong><span>{{ selectedGroup.owner_name || `#${selectedGroup.owner_id}` }}</span></div>
          <div><strong>Status</strong><span>{{ selectedGroup.status_label || selectedGroup.status }}</span></div>
          <div><strong>Freie Plätze</strong><span>{{ selectedGroup.free_slots }} von {{ selectedGroup.max_members }}</span></div>
          <div><strong>Mindest-Rate</strong><span>{{ selectedGroup.min_ship_rate ? `Rate ${selectedGroup.min_ship_rate} oder besser` : 'Keine Mindest-Rate' }}</span></div>
          <div><strong>Bevorzugtes Schiff</strong><span>{{ selectedGroup.ship_name || selectedGroup.ship_class || 'Beliebig' }}</span></div>
          <div><strong>Anonymer Beitritt</strong><span>{{ selectedGroup.allow_anonymous ? 'Erlaubt' : 'Nicht erlaubt' }}</span></div>
          <div v-if="selectedGroup.fleet_restriction"><strong>Flottenhinweis</strong><span>{{ selectedGroup.fleet_restriction }}</span></div>
          <div v-if="selectedGroup.scheduled_at"><strong>Termin</strong><span>{{ formatDate(selectedGroup.scheduled_at) }}</span></div>
          <div v-if="selectedGroup.expires_at"><strong>Läuft ab</strong><span>{{ formatDate(selectedGroup.expires_at) }}</span></div>
        </div>

        <h3>Teilnehmer</h3>
        <ul v-if="selectedGroup.participants.length" class="plain-list">
          <li v-for="participant in selectedGroup.participants" :key="participant.id">
            <strong>{{ participant.display_name }}</strong>
            <span class="muted">
              {{ participant.is_anonymous ? 'Gast' : 'Registriert' }}
              <template v-if="participant.fleet_name"> · {{ participant.fleet_name }}</template>
              <template v-if="participant.participant_role"> · Rolle: {{ participant.participant_role }}</template>
              <template v-if="participant.ship_name || participant.custom_ship_name"> · {{ participant.ship_name || participant.custom_ship_name }}</template>
              <template v-if="participant.ship_rate || participant.custom_ship_rate"> · Rate {{ participant.ship_rate || participant.custom_ship_rate }}</template>
            </span>
          </li>
        </ul>
        <p v-else class="muted">Noch keine Crew eingetragen.</p>

        <div v-if="selectedGroup.guest_join_token" class="page-info-panel">
          <h3>Gast-Link speichern</h3>
          <p class="muted">
            Dein anonymer Beitritt wurde gespeichert. Speichere diesen Token/Link lokal, damit du deine Teilnahme später
            verlassen kannst.
          </p>
          <code>{{ selectedGroup.guest_join_token }}</code>
        </div>

        <div class="actions">
          <button v-if="selectedGroup.can_join" class="button" type="button" @click="openJoinOverlay(selectedGroup)">Teilnehmen</button>
          <span v-else class="badge muted-badge">{{ selectedGroup.can_join_reason || 'Beitritt aktuell nicht möglich.' }}</span>
          <RouterLink v-if="selectedGroup.can_manage" class="button secondary" to="/group-management">Verwalten</RouterLink>
        </div>
      </template>
    </DetailOverlay>

    <GroupJoinOverlay
      :open="Boolean(joinOverlayGroup)"
      :group="joinOverlayGroup"
      :ships="ships"
      :is-authenticated="isAuthenticated"
      :submitting="joinSubmitting"
      @close="joinOverlayGroup = null"
      @submit="joinGroup"
    />
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'

import GroupCard from '@/components/groups/GroupCard.vue'
import DetailOverlay from '@/components/ui/DetailOverlay.vue'
import MessageBox from '@/components/ui/MessageBox.vue'
import { useSession } from '@/composables/useSession'
import GroupJoinOverlay from '@/components/groups/GroupJoinOverlay.vue'
import { groupService } from '@/services/groupService'
import { shipService } from '@/services/shipService'

const { isAuthenticated } = useSession()

const groups = ref([])
const ships = ref([])
const selectedGroup = ref(null)
const joinOverlayGroup = ref(null)
const joinSubmitting = ref(false)
const message = ref('')

async function loadGroups() {
  try {
    groups.value = await groupService.list()
    if (selectedGroup.value) {
      selectedGroup.value = groups.value.find((group) => group.id === selectedGroup.value.id) || null
    }
  } catch (error) {
    message.value = error.response?.data?.detail || 'Gruppen konnten nicht geladen werden. Läuft das Backend?'
  }
}

function selectGroup(group) {
  selectedGroup.value = group
}

function rememberGuestJoin(group) {
  if (!group.guest_join_token) {
    return
  }

  const stored = JSON.parse(localStorage.getItem('wosb_guest_group_tokens') || '[]')
  const next = stored.filter((item) => item.groupId !== group.id)
  next.push({
    groupId: group.id,
    groupTitle: group.title,
    joinToken: group.guest_join_token,
    savedAt: new Date().toISOString(),
  })
  localStorage.setItem('wosb_guest_group_tokens', JSON.stringify(next))
}

async function loadShips() {
  try {
    ships.value = await shipService.list()
  } catch (error) {
    message.value = error.response?.data?.detail || 'Schiffskatalog konnte nicht geladen werden.'
  }
}

function openJoinOverlay(group) {
  if (!group.can_join) {
    message.value = group.can_join_reason || 'Beitritt aktuell nicht möglich.'
    return
  }
  joinOverlayGroup.value = group
}

async function joinGroup(payload) {
  const group = joinOverlayGroup.value
  if (!group) {
    return
  }

  joinSubmitting.value = true
  try {
    const updated = await groupService.join(group.id, payload)
    rememberGuestJoin(updated)
    groups.value = groups.value.map((item) => (item.id === updated.id ? updated : item))
    selectedGroup.value = updated
    joinOverlayGroup.value = null
    message.value = isAuthenticated.value ? 'Du bist für die Gruppe angemeldet.' : 'Du bist als Gast für die Gruppe angemeldet.'
  } catch (error) {
    message.value = error.response?.data?.detail || 'Anmeldung zur Gruppe fehlgeschlagen.'
  } finally {
    joinSubmitting.value = false
  }
}

function formatDate(value) {
  return new Intl.DateTimeFormat('de-DE', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

onMounted(() => {
  loadGroups()
  loadShips()
})
</script>
