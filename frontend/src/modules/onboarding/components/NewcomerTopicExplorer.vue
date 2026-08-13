<script setup>
import { computed, ref, watch } from 'vue'
import AppIcon from '@/core/components/AppIcon.vue'
import { useLocale } from '@/locales'
import NewcomerFolderContent from '@/modules/onboarding/components/NewcomerFolderContent.vue'
import NewcomerFolderNavigation from '@/modules/onboarding/components/NewcomerFolderNavigation.vue'
import { resourceComponent, resourceTarget } from '@/modules/onboarding/domain/newcomerGuideDraft'
import { resourceIcon, topicKind, topicResourceCount, topicSummary } from '@/modules/onboarding/domain/newcomerGuidePresentation.js'

const props = defineProps({
  title: { type: String, required: true },
  intro: { type: String, default: '' },
  folders: { type: Array, default: () => [] },
  activeIndex: { type: Number, default: -1 },
})
const emit = defineEmits(['select', 'home'])
const { t } = useLocale()
const selectedResourceIndex = ref(-1)
const searchQuery = ref('')
const typeFilter = ref('all')

const activeFolder = computed(() => props.folders[props.activeIndex] || null)
const selectedResource = computed(() => activeFolder.value?.resources?.[selectedResourceIndex.value] || null)
const currentItemLabel = computed(() => selectedResource.value?.label || (activeFolder.value ? t('newcomerGuide.textSection') : ''))
const normalizedQuery = computed(() => searchQuery.value.trim().toLocaleLowerCase())
const filteredFolders = computed(() => props.folders
  .map((folder, index) => ({ folder, index }))
  .filter(({ folder }) => {
    const typeMatches = typeFilter.value === 'all'
      || (typeFilter.value === 'text' && folder.block_type === 'text')
      || (typeFilter.value !== 'text' && folder.resources?.some((resource) => resource.resource_type === typeFilter.value))
    const content = [folder.title, folder.body, ...(folder.resources || []).flatMap((resource) => [resource.label, resource.description])]
      .filter(Boolean).join(' ').toLocaleLowerCase()
    return typeMatches && (!normalizedQuery.value || content.includes(normalizedQuery.value))
  }))
const filteredResources = computed(() => (activeFolder.value?.resources || [])
  .map((resource, index) => ({ resource, index }))
  .filter(({ resource }) => {
    const typeMatches = typeFilter.value === 'all' || resource.resource_type === typeFilter.value
    const content = `${resource.label || ''} ${resource.description || ''}`.toLocaleLowerCase()
    return typeMatches && (!normalizedQuery.value || content.includes(normalizedQuery.value))
  }))
const showBriefing = computed(() => {
  if (!activeFolder.value || !['all', 'text'].includes(typeFilter.value)) return false
  const content = `${activeFolder.value.title || ''} ${activeFolder.value.body || ''}`.toLocaleLowerCase()
  return !normalizedQuery.value || content.includes(normalizedQuery.value)
})

watch([() => props.activeIndex, searchQuery, typeFilter], () => {
  const visibleResources = filteredResources.value
  if (!showBriefing.value) {
    selectedResourceIndex.value = visibleResources[0]?.index ?? -1
    return
  }
  if (selectedResourceIndex.value >= 0 && !visibleResources.some(({ index }) => index === selectedResourceIndex.value)) {
    selectedResourceIndex.value = -1
  }
}, { flush: 'sync' })

function selectFolder(index) {
  selectedResourceIndex.value = -1
  emit('select', index)
}

function showHome() {
  selectedResourceIndex.value = -1
  emit('home')
}
</script>

<template>
  <div class="newcomer-explorer">
    <header class="newcomer-explorer-toolbar">
      <div class="newcomer-explorer-history">
        <button type="button" :disabled="activeIndex < 0" :aria-label="t('newcomerGuide.explorer.back')" @click="showHome">
          <AppIcon name="chevron-left" :size="18" />
        </button>
        <button type="button" :disabled="activeIndex < 0" :aria-label="t('newcomerGuide.explorer.home')" @click="showHome">
          <AppIcon name="home" :size="17" />
        </button>
      </div>
      <div class="newcomer-explorer-address" :aria-label="t('newcomerGuide.explorer.addressLabel')">
        <button type="button" @click="showHome"><AppIcon name="folder" :size="17" />{{ title }}</button>
        <template v-if="activeFolder">
          <AppIcon name="chevron-right" :size="14" />
          <button type="button" @click="selectedResourceIndex = -1">{{ activeFolder.title }}</button>
        </template>
        <template v-if="selectedResource">
          <AppIcon name="chevron-right" :size="14" />
          <span aria-current="page">{{ currentItemLabel }}</span>
        </template>
      </div>
      <span class="newcomer-explorer-position">
        {{ activeFolder ? t('newcomerGuide.explorer.resourceCount', { count: (activeFolder.resources?.length || 0) + 1 }) : t('newcomerGuide.explorer.topicCount', { count: folders.length }) }}
      </span>
    </header>

    <div class="newcomer-explorer-filters" :aria-label="t('newcomerGuide.explorer.workspace')">
      <label class="newcomer-explorer-search">
        <AppIcon name="compass" :size="17" />
        <input v-model="searchQuery" type="search" :placeholder="t('guides.list.searchPlaceholder')" />
      </label>
      <label class="newcomer-explorer-type">
        <span>{{ t('common.type') }}</span>
        <select v-model="typeFilter">
          <option value="all">{{ t('common.all') }}</option>
          <option value="text">{{ t('newcomerGuide.textSection') }}</option>
          <option value="guide">{{ t('newcomerGuide.editor.types.guide') }}</option>
          <option value="build">{{ t('newcomerGuide.editor.types.build') }}</option>
          <option value="internal">{{ t('newcomerGuide.editor.types.internal') }}</option>
          <option value="external">{{ t('newcomerGuide.editor.types.external') }}</option>
        </select>
      </label>
    </div>

    <div class="newcomer-explorer-workspace">
      <NewcomerFolderNavigation
        :folders="folders"
        :active-index="activeIndex"
        :root-active="activeIndex < 0"
        show-root
        @root="showHome"
        @select="selectFolder"
      />

      <main class="newcomer-explorer-directory" aria-live="polite">
        <header class="newcomer-directory-heading">
          <div>
            <p class="eyebrow">{{ t('newcomerGuide.explorer.workspace') }}</p>
            <h2>{{ activeFolder?.title || t('newcomerGuide.explorer.topicsHeading') }}</h2>
          </div>
          <span class="summary-pill">{{ activeFolder ? t(`newcomerGuide.explorer.${topicKind(activeFolder)}`) : t('newcomerGuide.explorer.topicCount', { count: folders.length }) }}</span>
        </header>

        <div class="newcomer-directory-columns" aria-hidden="true">
          <span>{{ t('common.title') }}</span>
          <span>{{ t('common.type') }}</span>
        </div>

        <div v-if="!activeFolder" class="newcomer-directory-list">
          <button
            v-for="entry in filteredFolders"
            :key="entry.folder.id"
            class="newcomer-directory-row"
            type="button"
            @click="selectFolder(entry.index)"
          >
            <span class="newcomer-directory-row__icon"><AppIcon name="folder" :size="24" /></span>
            <span class="newcomer-directory-row__copy">
              <strong>{{ entry.folder.title }}</strong>
              <small>{{ topicSummary(entry.folder, t('newcomerGuide.explorer.noSummary')) }}</small>
            </span>
            <span class="newcomer-directory-row__type">{{ t(`newcomerGuide.explorer.${topicKind(entry.folder)}`) }}</span>
            <span class="newcomer-directory-row__meta">{{ t('newcomerGuide.explorer.resourceCount', { count: topicResourceCount(entry.folder) + 1 }) }}</span>
            <AppIcon name="chevron-right" :size="17" />
          </button>
          <p v-if="!filteredFolders.length" class="muted newcomer-directory-empty">{{ t('newcomerGuide.emptyFolders') }}</p>
        </div>

        <div v-else class="newcomer-directory-list">
          <button
            v-if="showBriefing"
            class="newcomer-directory-row"
            :class="{ 'is-selected': selectedResourceIndex < 0 }"
            type="button"
            @click="selectedResourceIndex = -1"
          >
            <span class="newcomer-directory-row__icon is-document"><AppIcon name="guides" :size="22" /></span>
            <span class="newcomer-directory-row__copy">
              <strong>{{ t('newcomerGuide.textSection') }}</strong>
              <small>{{ topicSummary(activeFolder, t('newcomerGuide.explorer.noSummary')) }}</small>
            </span>
            <span class="newcomer-directory-row__type">{{ t('newcomerGuide.explorer.text') }}</span>
            <span class="newcomer-directory-row__meta">{{ t('newcomerGuide.explorer.available') }}</span>
            <AppIcon name="chevron-right" :size="17" />
          </button>
          <button
            v-for="entry in filteredResources"
            :key="entry.resource.id"
            class="newcomer-directory-row"
            :class="{ 'is-selected': selectedResourceIndex === entry.index, 'is-unavailable': !entry.resource.available }"
            type="button"
            :disabled="!entry.resource.available"
            @click="selectedResourceIndex = entry.index"
          >
            <span class="newcomer-directory-row__icon"><AppIcon :name="resourceIcon(entry.resource)" :size="21" /></span>
            <span class="newcomer-directory-row__copy">
              <strong>{{ entry.resource.label }}</strong>
              <small>{{ entry.resource.description || t('newcomerGuide.explorer.noResourceDescription') }}</small>
            </span>
            <span class="newcomer-directory-row__type">{{ t(`newcomerGuide.editor.types.${entry.resource.resource_type}`) }}</span>
            <span class="newcomer-directory-row__meta">{{ entry.resource.available ? t('newcomerGuide.explorer.available') : t('newcomerGuide.unavailable') }}</span>
            <AppIcon name="chevron-right" :size="17" />
          </button>
          <p v-if="!showBriefing && !filteredResources.length" class="muted newcomer-directory-empty">{{ t('newcomerGuide.explorer.noResources') }}</p>
        </div>
      </main>

      <aside class="newcomer-explorer-preview">
        <div v-if="!activeFolder" class="newcomer-preview-welcome">
          <span class="newcomer-preview-icon"><AppIcon name="compass" :size="30" /></span>
          <p class="eyebrow">{{ t('newcomerGuide.explorer.workspace') }}</p>
          <h2>{{ title }}</h2>
          <p>{{ intro || t('newcomerGuide.explorer.topicsHint') }}</p>
          <dl>
            <div><dt>{{ t('newcomerGuide.folders') }}</dt><dd>{{ folders.length }}</dd></div>
            <div><dt>{{ t('newcomerGuide.explorer.resources') }}</dt><dd>{{ folders.reduce((total, folder) => total + topicResourceCount(folder), 0) }}</dd></div>
          </dl>
        </div>

        <NewcomerFolderContent v-else-if="!selectedResource" :folder="activeFolder" :show-resources="false" />

        <article v-else class="newcomer-resource-preview">
          <span class="newcomer-preview-icon"><AppIcon :name="resourceIcon(selectedResource)" :size="28" /></span>
          <p class="eyebrow">{{ t(`newcomerGuide.editor.types.${selectedResource.resource_type}`) }}</p>
          <h2>{{ selectedResource.label }}</h2>
          <p>{{ selectedResource.description || t('newcomerGuide.explorer.noResourceDescription') }}</p>
          <dl>
            <div><dt>{{ t('common.type') }}</dt><dd>{{ t(`newcomerGuide.editor.types.${selectedResource.resource_type}`) }}</dd></div>
            <div><dt>{{ t('newcomerGuide.explorer.available') }}</dt><dd>{{ selectedResource.available ? t('newcomerGuide.explorer.available') : t('newcomerGuide.unavailable') }}</dd></div>
          </dl>
          <component
            :is="resourceComponent(selectedResource)"
            v-bind="resourceTarget(selectedResource)"
            class="form-button primary-action newcomer-preview-open"
          >
            {{ t('newcomerGuide.open') }}
            <AppIcon name="arrow-right" :size="17" />
          </component>
        </article>
      </aside>
    </div>

    <footer class="newcomer-explorer-statusbar">
      <span>{{ activeFolder ? activeFolder.title : t('newcomerGuide.explorer.home') }}</span>
      <span>{{ activeFolder ? t('newcomerGuide.explorer.resourceCount', { count: (activeFolder.resources?.length || 0) + 1 }) : t('newcomerGuide.explorer.topicCount', { count: folders.length }) }}</span>
    </footer>
  </div>
</template>
