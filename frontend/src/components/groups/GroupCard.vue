<template>
  <article class="list-item clickable group-card" tabindex="0" @click="$emit('select', group)" @keydown.enter="$emit('select', group)">
    <div class="list-item-header">
      <div>
        <span class="badge">{{ group.focus_label || group.focus }}</span>
        <h3>{{ group.title }}</h3>
      </div>
      <div class="group-status-stack">
        <span class="badge" :class="`status-${group.status}`">{{ group.status_label || group.status }}</span>
        <span class="muted">{{ group.participant_count }}/{{ group.max_members }}</span>
      </div>
    </div>

    <p class="muted group-description">{{ group.description || 'Keine Beschreibung hinterlegt.' }}</p>

    <div class="group-meta-grid">
      <span><strong>Leitung:</strong> {{ group.owner_name || `#${group.owner_id}` }}</span>
      <span><strong>Min. Rate:</strong> {{ group.min_ship_rate ? `Rate ${group.min_ship_rate} oder besser` : 'Keine' }}</span>
      <span><strong>Bevorzugtes Schiff:</strong> {{ group.ship_name || group.ship_class || 'Beliebig' }}</span>
      <span><strong>Anonym:</strong> {{ group.allow_anonymous ? 'erlaubt' : 'nur Login' }}</span>
      <span v-if="group.fleet_restriction"><strong>Flotte:</strong> {{ group.fleet_restriction }}</span>
      <span v-if="group.scheduled_at"><strong>Termin:</strong> {{ formatDate(group.scheduled_at) }}</span>
      <span v-if="group.expires_at"><strong>Läuft ab:</strong> {{ formatDate(group.expires_at) }}</span>
      <span><strong>Freie Plätze:</strong> {{ group.free_slots }}</span>
    </div>

    <div class="crew-preview">
      <strong>Crew:</strong>
      <span class="muted">{{ crewLabel }}</span>
    </div>

    <div class="item-actions">
      <button class="button small secondary" type="button" @click.stop="$emit('select', group)">Details</button>
      <button v-if="group.can_join" class="button small" type="button" @click.stop="$emit('join', group)">Teilnehmen</button>
      <span v-else-if="group.is_joined" class="badge">Angemeldet</span>
      <span v-else-if="group.can_join_reason" class="badge muted-badge">{{ group.can_join_reason }}</span>
      <span v-if="group.can_manage" class="badge">Verwaltbar</span>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  group: {
    type: Object,
    required: true,
  },
})

defineEmits(['select', 'join'])

const crewLabel = computed(() => (props.group.members?.length ? props.group.members.join(', ') : 'Noch keine Crew eingetragen'))

function formatDate(value) {
  return new Intl.DateTimeFormat('de-DE', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}
</script>
