<script setup>
import { computed, ref } from 'vue'
import AppIcon from '@/core/components/AppIcon.vue'
import { useLocale } from '@/locales'
import NewcomerFolderContent from '@/modules/onboarding/components/NewcomerFolderContent.vue'
import NewcomerFolderNavigation from '@/modules/onboarding/components/NewcomerFolderNavigation.vue'
import { topicKind, topicResourceCount, topicSummary } from '@/modules/onboarding/domain/newcomerGuidePresentation.js'

const props = defineProps({
  title: { type: String, required: true },
  intro: { type: String, default: '' },
  folders: { type: Array, default: () => [] },
  activeIndex: { type: Number, default: -1 },
})
const emit = defineEmits(['select', 'home'])
const { t } = useLocale()
const searchQuery = ref('')
const typeFilter = ref('all')

const activeFolder = computed(() => props.folders[props.activeIndex] || null)
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
const previousFolder = computed(() => props.activeIndex > 0 ? props.folders[props.activeIndex - 1] : null)
const nextFolder = computed(() => props.activeIndex >= 0 && props.activeIndex < props.folders.length - 1
  ? props.folders[props.activeIndex + 1]
  : null)
const resourceTotal = computed(() => props.folders.reduce((total, folder) => total + topicResourceCount(folder), 0))

function selectFolder(index) {
  emit('select', Number(index))
}
</script>

<template>
  <div class="newcomer-explorer">
    <header class="newcomer-explorer-toolbar">
      <div class="newcomer-explorer-history">
        <button type="button" :disabled="activeIndex < 0" :aria-label="t('newcomerGuide.explorer.back')" @click="$emit('home')">
          <AppIcon name="chevron-left" :size="18" />
        </button>
        <button type="button" :aria-label="t('newcomerGuide.explorer.home')" @click="$emit('home')">
          <AppIcon name="home" :size="17" />
        </button>
      </div>
      <div class="newcomer-explorer-address" :aria-label="t('newcomerGuide.explorer.addressLabel')">
        <button type="button" @click="$emit('home')"><AppIcon name="folder" :size="17" />{{ title }}</button>
        <template v-if="activeFolder">
          <AppIcon name="chevron-right" :size="14" />
          <span aria-current="page">{{ activeFolder.title }}</span>
        </template>
      </div>
      <span class="newcomer-explorer-position">
        {{ activeFolder ? t('newcomerGuide.folderPosition', { current: activeIndex + 1, total: folders.length }) : t('newcomerGuide.explorer.topicCount', { count: folders.length }) }}
      </span>
    </header>

    <div v-if="!activeFolder" class="newcomer-explorer-filters" :aria-label="t('newcomerGuide.explorer.workspace')">
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

    <label class="newcomer-mobile-topic-picker">
      <span>{{ t('newcomerGuide.folders') }}</span>
      <select :value="activeIndex" @change="$event.target.value === '-1' ? $emit('home') : selectFolder($event.target.value)">
        <option value="-1">{{ t('newcomerGuide.explorer.home') }}</option>
        <option v-for="(folder, index) in folders" :key="folder.id" :value="index">{{ index + 1 }}. {{ folder.title }}</option>
      </select>
    </label>

    <div class="newcomer-explorer-workspace">
      <NewcomerFolderNavigation
        :folders="folders" :active-index="activeIndex" :root-active="activeIndex < 0" show-root
        @root="$emit('home')" @select="selectFolder"
      />

      <main class="newcomer-reader" aria-live="polite">
        <section v-if="!activeFolder" class="newcomer-explorer-home">
          <header class="newcomer-reader-hero">
            <span class="newcomer-preview-icon"><AppIcon name="compass" :size="30" /></span>
            <div>
              <p class="eyebrow">{{ t('newcomerGuide.explorer.workspace') }}</p>
              <h2>{{ t('newcomerGuide.explorer.topicsHeading') }}</h2>
              <p>{{ intro || t('newcomerGuide.explorer.topicsHint') }}</p>
            </div>
            <div class="newcomer-reader-stats">
              <span><strong>{{ folders.length }}</strong>{{ t('newcomerGuide.folders') }}</span>
              <span><strong>{{ resourceTotal }}</strong>{{ t('newcomerGuide.explorer.resources') }}</span>
            </div>
          </header>

          <div class="newcomer-topic-grid">
            <button
              v-for="entry in filteredFolders" :key="entry.folder.id" class="newcomer-topic-card" type="button"
              @click="selectFolder(entry.index)"
            >
              <span class="newcomer-topic-card__index">{{ String(entry.index + 1).padStart(2, '0') }}</span>
              <span class="newcomer-topic-card__copy">
                <strong>{{ entry.folder.title }}</strong>
                <small>{{ topicSummary(entry.folder, t('newcomerGuide.explorer.noSummary')) }}</small>
              </span>
              <span class="newcomer-topic-card__meta">
                {{ t(`newcomerGuide.explorer.${topicKind(entry.folder)}`) }} · {{ t('newcomerGuide.explorer.resourceCount', { count: topicResourceCount(entry.folder) }) }}
              </span>
              <AppIcon name="arrow-right" :size="18" />
            </button>
            <p v-if="!filteredFolders.length" class="muted newcomer-directory-empty">{{ t('newcomerGuide.emptyFolders') }}</p>
          </div>
        </section>

        <article v-else class="newcomer-reader-article">
          <NewcomerFolderContent :folder="activeFolder" />
          <nav class="newcomer-topic-progress" :aria-label="t('newcomerGuide.explorer.topicNavigation')">
            <button v-if="previousFolder" type="button" @click="selectFolder(activeIndex - 1)">
              <AppIcon name="chevron-left" :size="17" />
              <span><small>{{ t('newcomerGuide.explorer.previous') }}</small><strong>{{ previousFolder.title }}</strong></span>
            </button>
            <button v-if="nextFolder" type="button" @click="selectFolder(activeIndex + 1)">
              <span><small>{{ t('newcomerGuide.explorer.next') }}</small><strong>{{ nextFolder.title }}</strong></span>
              <AppIcon name="chevron-right" :size="17" />
            </button>
          </nav>
        </article>
      </main>
    </div>

    <footer class="newcomer-explorer-statusbar">
      <span>{{ activeFolder ? activeFolder.title : t('newcomerGuide.explorer.home') }}</span>
      <span>{{ activeFolder ? t('newcomerGuide.folderPosition', { current: activeIndex + 1, total: folders.length }) : t('newcomerGuide.explorer.topicCount', { count: folders.length }) }}</span>
    </footer>
  </div>
</template>
