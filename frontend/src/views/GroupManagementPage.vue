<template>
  <section class="management-flow">
    <div class="card management-list-card">
      <div class="section-heading">
        <span class="badge">Gruppenverwaltung</span>
        <h1>Gruppenverwaltung</h1>
        <p class="muted">
          Hier erscheinen nur Gruppen, die du laut Backend verwalten darfst. Schließen archiviert die Gruppe; sie verschwindet
          danach aus der öffentlichen Übersicht, bleibt aber für Admins nachvollziehbar.
        </p>
      </div>

      <div class="actions compact-actions">
        <button class="button" type="button" @click="showCreateOverlay = true">Neue Gruppe anlegen</button>
      </div>

      <MessageBox :message="message" />

      <div class="list-section-header">
        <div>
          <h2>Verwaltbare Gruppen</h2>
          <p class="muted">Eigene Gruppen und für Admins zusätzlich alle Gruppen.</p>
        </div>
        <span class="badge">{{ groups.length }} Gruppen</span>
      </div>

      <div class="list">
        <article v-for="group in groups" :key="group.id" class="list-item clickable" @click="selectGroup(group)">
          <div class="list-item-header">
            <div>
              <span class="badge">{{ group.focus_label || group.focus }}</span>
              <h3>{{ group.title }}</h3>
              <p class="muted">Leitung: {{ group.owner_name || `#${group.owner_id}` }}</p>
              <p class="muted">{{ group.description }}</p>
              <p class="muted">
                {{ group.participant_count }}/{{ group.max_members }} Teilnehmer · {{ group.status_label || group.status }}
                <template v-if="group.expires_at"> · läuft ab {{ formatDate(group.expires_at) }}</template>
              </p>
            </div>
            <button v-if="group.active" class="button danger" type="button" @click.stop="closeGroup(group.id)">Schließen</button>
            <span v-else class="badge muted-badge">Archiviert</span>
          </div>
        </article>
      </div>
    </div>

    <GroupFormOverlay :open="showCreateOverlay" @submit="createGroup" @close="showCreateOverlay = false" />

    <DetailOverlay :open="Boolean(selectedGroup)" :title="selectedGroup?.title || ''" :eyebrow="'Gruppenverwaltung'" @close="selectedGroup = null">
      <template v-if="selectedGroup">
        <p class="muted">{{ selectedGroup.description }}</p>
        <div class="detail-grid">
          <div><strong>Fokus</strong><span>{{ selectedGroup.focus_label || selectedGroup.focus }}</span></div>
          <div><strong>Leitung</strong><span>{{ selectedGroup.owner_name || `#${selectedGroup.owner_id}` }}</span></div>
          <div><strong>Teilnehmer</strong><span>{{ selectedGroup.participant_count }}/{{ selectedGroup.max_members }}</span></div>
          <div><strong>Status</strong><span>{{ selectedGroup.status_label || selectedGroup.status }}</span></div>
          <div><strong>Mindest-Rate</strong><span>{{ selectedGroup.min_ship_rate ? `Rate ${selectedGroup.min_ship_rate} oder besser` : 'Keine' }}</span></div>
          <div><strong>Bevorzugtes Schiff</strong><span>{{ selectedGroup.ship_name || selectedGroup.ship_class }}</span></div>
          <div><strong>Anonym</strong><span>{{ selectedGroup.allow_anonymous ? 'Erlaubt' : 'Deaktiviert' }}</span></div>
          <div v-if="selectedGroup.expires_at"><strong>Ablauf</strong><span>{{ formatDate(selectedGroup.expires_at) }}</span></div>
        </div>
        <h3>Teilnehmer</h3>
        <ul class="plain-list">
          <li v-for="participant in selectedGroup.participants" :key="participant.id">
            <strong>{{ participant.display_name }}</strong>
            <span class="muted">
              {{ participant.is_anonymous ? 'Gast' : 'Registriert' }} · {{ participant.status }}
              <template v-if="participant.fleet_name"> · {{ participant.fleet_name }}</template>
              <template v-if="participant.participant_role"> · Rolle: {{ participant.participant_role }}</template>
              <template v-if="participant.ship_name || participant.custom_ship_name"> · {{ participant.ship_name || participant.custom_ship_name }}</template>
              <template v-if="participant.ship_rate || participant.custom_ship_rate"> · Rate {{ participant.ship_rate || participant.custom_ship_rate }}</template>
            </span>
          </li>
        </ul>
        <div class="actions">
          <button v-if="selectedGroup.active" class="button danger" type="button" @click="closeGroup(selectedGroup.id)">Gruppe schließen</button>
        </div>
      </template>
    </DetailOverlay>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'

import GroupFormOverlay from '@/components/groups/GroupFormOverlay.vue'
import DetailOverlay from '@/components/ui/DetailOverlay.vue'
import MessageBox from '@/components/ui/MessageBox.vue'
import { groupService } from '@/services/groupService'

const groups = ref([])
const selectedGroup = ref(null)
const showCreateOverlay = ref(false)
const message = ref('')

async function loadGroups() {
  try {
    groups.value = await groupService.manageable()
    if (selectedGroup.value) {
      selectedGroup.value = groups.value.find((group) => group.id === selectedGroup.value.id) || null
    }
  } catch (error) {
    message.value = error.response?.data?.detail || 'Verwaltbare Gruppen konnten nicht geladen werden.'
  }
}

function selectGroup(group) {
  selectedGroup.value = group
}

async function createGroup(payload) {
  try {
    const created = await groupService.create(payload)
    groups.value = [created, ...groups.value]
    selectedGroup.value = created
    showCreateOverlay.value = false
    message.value = 'Gruppe wurde angelegt.'
  } catch (error) {
    message.value = error.response?.data?.detail || 'Gruppe konnte nicht angelegt werden.'
  }
}

async function closeGroup(id) {
  try {
    const updated = await groupService.close(id)
    groups.value = groups.value.map((group) => (group.id === updated.id ? updated : group))
    selectedGroup.value = updated
    message.value = 'Gruppe wurde geschlossen und archiviert.'
  } catch (error) {
    message.value = error.response?.data?.detail || 'Gruppe konnte nicht geschlossen werden.'
  }
}

function formatDate(value) {
  return new Intl.DateTimeFormat('de-DE', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

onMounted(loadGroups)
</script>
