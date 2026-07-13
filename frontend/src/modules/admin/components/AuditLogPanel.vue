<script setup>
import { computed, onMounted, ref, watch } from 'vue'

import { useLocale } from '@/locales'
import { listAuditLogs } from '@/modules/admin/api/admin'

const { locale, t } = useLocale()
const rows = ref([])
const loading = ref(false)
const error = ref('')
const entityType = ref('')
const action = ref('')
const actor = ref('')
const fromDate = ref('')
const toDate = ref('')
let timer = null

const groupedRows = computed(() => {
  const groups = []
  for (const row of rows.value) {
    const day = new Intl.DateTimeFormat(locale.value, { dateStyle: 'full' }).format(new Date(row.created_at))
    let group = groups.find((item) => item.day === day)
    if (!group) {
      group = { day, rows: [] }
      groups.push(group)
    }
    group.rows.push(row)
  }
  return groups
})

function formatTime(value) {
  return new Intl.DateTimeFormat(locale.value, { timeStyle: 'medium' }).format(new Date(value))
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    rows.value = await listAuditLogs({
      entityType: entityType.value,
      action: action.value,
      actor: actor.value,
      fromDate: fromDate.value,
      toDate: toDate.value,
      limit: 300,
    })
  } catch (err) {
    error.value = err.message || t('admin.audit.loadError')
  } finally {
    loading.value = false
  }
}

watch([entityType, action, fromDate, toDate], load)
watch(actor, () => {
  window.clearTimeout(timer)
  timer = window.setTimeout(load, 240)
})
onMounted(load)
</script>

<template>
  <section class="audit-log-panel">
    <div class="admin-panel-heading"><div><h2>{{ t('admin.audit.title') }}</h2><p>{{ t('admin.audit.subtitle') }}</p></div><span class="summary-pill">{{ rows.length }}</span></div>
    <div class="staff-filter-row audit-filter-row">
      <label class="filter-box select-shell"><select v-model="entityType"><option value="">{{ t('admin.audit.allEntities') }}</option><option value="build">{{ t('admin.audit.entities.build') }}</option><option value="forum_thread">{{ t('admin.audit.entities.forum_thread') }}</option><option value="forum_post">{{ t('admin.audit.entities.forum_post') }}</option><option value="guide">{{ t('admin.audit.entities.guide') }}</option><option value="newcomer_guide">{{ t('admin.audit.entities.newcomer_guide') }}</option></select></label>
      <label class="filter-box select-shell"><select v-model="action"><option value="">{{ t('admin.audit.allActions') }}</option><option value="create">{{ t('admin.audit.actions.create') }}</option><option value="update">{{ t('admin.audit.actions.update') }}</option><option value="delete">{{ t('admin.audit.actions.delete') }}</option></select></label>
      <label class="filter-box admin-search"><input v-model="actor" type="search" :placeholder="t('admin.audit.actorPlaceholder')" /></label>
      <label class="filter-box"><input v-model="fromDate" type="date" :aria-label="t('admin.security.from')" /></label>
      <label class="filter-box"><input v-model="toDate" type="date" :aria-label="t('admin.security.to')" /></label>
      <button class="small-action" type="button" :disabled="loading" @click="load">{{ t('admin.logs.refresh') }}</button>
    </div>
    <p v-if="loading" class="muted table-state">{{ t('admin.audit.loading') }}</p>
    <p v-else-if="error" class="error-text table-state">{{ error }}</p>
    <p v-else-if="rows.length === 0" class="muted table-state">{{ t('admin.audit.empty') }}</p>
    <div v-else class="audit-day-groups">
      <section v-for="group in groupedRows" :key="group.day" class="audit-day-group">
        <h3>{{ group.day }}</h3>
        <article v-for="row in group.rows" :key="row.id" class="audit-row">
          <span class="audit-action" :class="`audit-${row.action}`">{{ t(`admin.audit.actions.${row.action}`) }}</span>
          <div><strong>{{ row.summary }}</strong><small>{{ formatTime(row.created_at) }} · {{ row.actor_username }} ({{ t(`roles.${row.actor_role}`) }}) · {{ t(`admin.audit.entities.${row.entity_type}`) }} #{{ row.entity_id }}</small><small v-if="row.changed_fields.length">{{ t('admin.audit.fields') }}: {{ row.changed_fields.join(', ') }}</small></div>
        </article>
      </section>
    </div>
  </section>
</template>
