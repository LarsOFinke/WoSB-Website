<script setup>
import { onMounted, reactive, ref } from 'vue'

import { useLocale } from '@/locales'
import {
  createWarehousePort,
  deactivateWarehousePort,
  listAdminWarehousePorts,
  updateWarehousePort,
} from '@/modules/warehouse/api/warehouse'

const emit = defineEmits(['count-change'])
const { t } = useLocale()
const ports = ref([])
const editingId = ref(null)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref('')
const form = reactive({ name: '', sort_order: 100, is_active: true })

function reset(row = null) {
  editingId.value = row?.id || null
  Object.assign(form, {
    name: row?.name || '',
    sort_order: row?.sort_order ?? 100,
    is_active: row?.is_active ?? true,
  })
  error.value = ''
  success.value = ''
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    ports.value = await listAdminWarehousePorts()
    emit('count-change', ports.value.length)
  } catch (err) {
    error.value = err.message || t('masterData.ports.loadError')
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  error.value = ''
  success.value = ''
  const payload = { name: form.name.trim(), sort_order: Number(form.sort_order), is_active: form.is_active }
  try {
    if (editingId.value) await updateWarehousePort(editingId.value, payload)
    else await createWarehousePort(payload)
    await load()
    reset()
    success.value = t('masterData.ports.saved')
  } catch (err) {
    error.value = err.message || t('masterData.ports.saveError')
  } finally {
    saving.value = false
  }
}

async function deactivate(row) {
  saving.value = true
  error.value = ''
  try {
    await deactivateWarehousePort(row.id)
    await load()
    if (editingId.value === row.id) reset()
    success.value = t('masterData.ports.deactivated')
  } catch (err) {
    error.value = err.message || t('masterData.ports.saveError')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="master-data-workspace">
    <aside class="catalog-panel">
      <header class="catalog-panel-header">
        <div><span class="panel-kicker">{{ ports.length }}</span><h2>{{ t('masterData.ports.title') }}</h2></div>
        <button class="small-action" type="button" @click="reset()">{{ t('masterData.new') }}</button>
      </header>
      <div class="catalog-scroll">
        <article v-for="port in ports" :key="port.id" class="catalog-record" :class="{ 'is-selected': editingId === port.id, 'is-inactive': !port.is_active }">
          <button class="catalog-record-main" type="button" @click="reset(port)">
            <span class="record-icon">⚓</span>
            <span class="record-copy"><strong>{{ port.name }}</strong><small>{{ t('masterData.ports.order', { value: port.sort_order }) }}</small></span>
          </button>
          <div class="record-meta">
            <span class="status-chip">{{ port.is_active ? t('masterData.ports.active') : t('masterData.ports.inactive') }}</span>
            <button v-if="port.is_active" class="danger-action" type="button" :disabled="saving" @click="deactivate(port)">{{ t('masterData.deactivate') }}</button>
          </div>
        </article>
      </div>
    </aside>

    <form class="editor-panel" @submit.prevent="save">
      <header class="editor-header">
        <div><span class="panel-kicker">{{ t('masterData.ports.catalog') }}</span><h2>{{ editingId ? t('masterData.ports.edit') : t('masterData.ports.create') }}</h2></div>
      </header>
      <p>{{ t('masterData.ports.hint') }}</p>
      <div class="editor-section form-grid two-columns">
        <label><span>{{ t('warehouse.fields.port') }}</span><input v-model="form.name" required maxlength="120" /></label>
        <label><span>{{ t('masterData.fields.sortOrder') }}</span><input v-model.number="form.sort_order" type="number" min="0" max="100000" required /></label>
        <label class="toggle-field"><input v-model="form.is_active" type="checkbox" /><span>{{ t('masterData.fields.active') }}</span></label>
      </div>
      <p v-if="loading" class="notice-card muted">{{ t('masterData.loading') }}</p>
      <p v-if="error" class="notice-card error-text" role="alert">{{ error }}</p>
      <p v-if="success" class="notice-card success-text" role="status">{{ success }}</p>
      <footer class="editor-actions"><button class="form-button primary-action" type="submit" :disabled="saving">{{ t('common.save') }}</button></footer>
    </form>
  </section>
</template>
