<template>
  <section class="grid grid-2">
    <div class="card">
      <span class="badge">Admin</span>
      <h1>Admin-Panel</h1>
      <p class="muted">Dieser Bereich wird serverseitig über die Rolle <strong>admin</strong> freigeschaltet.</p>
      <MessageBox :message="message" />

      <div class="list">
        <article v-for="group in groups" :key="group.id" class="list-item clickable" @click="selectedGroup = group">
          <div class="list-item-header">
            <div>
              <span class="badge">{{ group.ship_class }}</span>
              <h3>{{ group.title }}</h3>
              <p class="muted">Leitung: {{ group.owner_name || `#${group.owner_id}` }}</p>
              <p class="muted">Crew: {{ group.participant_count }}/{{ group.max_members }}</p>
            </div>
            <RouterLink class="button small secondary" to="/group-management" @click.stop>Verwaltung</RouterLink>
          </div>
        </article>
      </div>
    </div>

    <aside class="card">
      <h2>Admin-Rechte</h2>
      <p class="muted">
        Das Frontend blendet den Bereich nur für Admins ein. Der eigentliche Schutz sitzt im Backend unter
        <code>/api/v1/admin/*</code> und prüft die Rolle erneut.
      </p>
    </aside>

    <DetailOverlay :open="Boolean(selectedGroup)" :title="selectedGroup?.title || ''" eyebrow="Admin-Details" @close="selectedGroup = null">
      <template v-if="selectedGroup">
        <div class="detail-grid">
          <div><strong>ID</strong><span>#{{ selectedGroup.id }}</span></div>
          <div><strong>Owner</strong><span>{{ selectedGroup.owner_name || selectedGroup.owner_id }}</span></div>
          <div><strong>Status</strong><span>{{ selectedGroup.status }}</span></div>
          <div><strong>Verwaltbar</strong><span>{{ selectedGroup.can_manage ? 'Ja' : 'Nein' }}</span></div>
        </div>
        <p class="muted">{{ selectedGroup.description }}</p>
      </template>
    </DetailOverlay>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'

import DetailOverlay from '@/components/ui/DetailOverlay.vue'
import MessageBox from '@/components/ui/MessageBox.vue'
import { adminService } from '@/services/adminService'

const groups = ref([])
const selectedGroup = ref(null)
const message = ref('')

async function loadGroups() {
  try {
    groups.value = await adminService.listGroups()
  } catch (error) {
    message.value = error.response?.data?.detail || 'Admin-Gruppen konnten nicht geladen werden.'
  }
}

onMounted(loadGroups)
</script>
