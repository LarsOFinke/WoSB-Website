<script setup>
import { computed, reactive, ref, watch } from 'vue'

import { useLocale } from '@/locales'
import { buildEmbedLayouts } from '@/shared/content/richTextEmbeds'

const props = defineProps({
  builds: {
    type: Array,
    default: () => [],
  },
  linkedBuilds: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['link', 'unlink', 'insert'])
const { t } = useLocale()
const selectedBuildId = ref('')
const layoutById = reactive({})

const selectedBuild = computed(() => props.builds.find((build) => Number(build.id) === Number(selectedBuildId.value)))
const linkedIds = computed(() => new Set(props.linkedBuilds.map((build) => Number(build.id))))

watch(() => props.builds, (builds) => {
  if (!selectedBuildId.value && builds.length) selectedBuildId.value = String(builds[0].id)
}, { immediate: true })

function currentLayout(buildId) {
  return layoutById[buildId] || 'card'
}

function setLayout(buildId, value) {
  layoutById[buildId] = value
}

function linkSelected() {
  if (!selectedBuild.value) return
  emit('link', selectedBuild.value)
}

function insertSelected() {
  if (!selectedBuild.value) return
  emit('insert', { build: selectedBuild.value, layout: currentLayout(selectedBuild.value.id) })
}

function shipLine(build) {
  return `${build.ship?.name || '—'} · ${t('common.rate')} ${build.ship?.rate || '—'} · ${t(`builds.types.${build.build_type || 'balanced'}`)}`
}
</script>

<template>
  <div class="build-insert-panel" :aria-label="t('buildEmbeds.tools')">
    <div class="build-insert-heading">
      <div>
        <strong>{{ t('buildEmbeds.tools') }}</strong>
        <span>{{ t('buildEmbeds.toolsHint') }}</span>
      </div>
      <RouterLink class="small-action" to="/builds/new">{{ t('buildEmbeds.createBuild') }}</RouterLink>
    </div>

    <div class="build-insert-controls">
      <label class="select-shell full-select-shell">
        <select v-model="selectedBuildId" :disabled="loading || !builds.length">
          <option v-if="loading" value="">{{ t('buildEmbeds.loading') }}</option>
          <option v-else-if="!builds.length" value="">{{ t('buildEmbeds.empty') }}</option>
          <option v-for="build in builds" v-else :key="build.id" :value="build.id">
            {{ build.build_name }} · {{ build.ship?.name }}
          </option>
        </select>
      </label>

      <label class="select-shell compact-select-shell build-layout-select">
        <select :value="selectedBuild ? currentLayout(selectedBuild.id) : 'card'" :disabled="!selectedBuild" @change="selectedBuild && setLayout(selectedBuild.id, $event.target.value)">
          <option v-for="layout in buildEmbedLayouts" :key="layout" :value="layout">{{ t(`buildEmbeds.layouts.${layout}`) }}</option>
        </select>
      </label>

      <button class="small-action" type="button" :disabled="!selectedBuild" @click="linkSelected">
        {{ t('buildEmbeds.linkBuild') }}
      </button>
      <button class="small-action primary" type="button" :disabled="!selectedBuild" @click="insertSelected">
        {{ t('buildEmbeds.insertInline') }}
      </button>
    </div>

    <article v-if="selectedBuild" class="build-insert-preview">
      <div>
        <span class="eyebrow">{{ t('buildEmbeds.selected') }}</span>
        <strong>{{ selectedBuild.build_name }}</strong>
        <small>{{ shipLine(selectedBuild) }}</small>
      </div>
      <span class="status-pill" :class="{ 'is-success': linkedIds.has(Number(selectedBuild.id)) }">
        {{ linkedIds.has(Number(selectedBuild.id)) ? t('buildEmbeds.alreadyLinked') : t('buildEmbeds.notLinked') }}
      </span>
    </article>

    <div v-if="linkedBuilds.length" class="linked-build-list">
      <strong>{{ t('buildEmbeds.linkedTitle') }}</strong>
      <article v-for="build in linkedBuilds" :key="build.id" class="linked-build-row">
        <div>
          <strong>{{ build.build_name }}</strong>
          <span>{{ shipLine(build) }}</span>
        </div>
        <div class="attachment-insert-actions">
          <RouterLink class="small-action" :to="`/builds/${build.id}`">{{ t('buildEmbeds.openBuild') }}</RouterLink>
          <button class="chip-remove" type="button" @click="emit('unlink', build.id)">× {{ t('buildEmbeds.unlinkBuild') }}</button>
        </div>
      </article>
    </div>
  </div>
</template>
