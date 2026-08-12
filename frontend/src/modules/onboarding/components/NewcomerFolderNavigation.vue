<script setup>
import AppIcon from '@/core/components/AppIcon.vue'
import { useLocale } from '@/locales'

defineProps({
  folders: { type: Array, default: () => [] },
  activeIndex: { type: Number, default: 0 },
  editable: { type: Boolean, default: false },
})

defineEmits(['select', 'move', 'remove'])
const { t } = useLocale()
</script>

<template>
  <nav class="newcomer-folder-navigation" :aria-label="t('newcomerGuide.folderNavigation')">
    <div class="newcomer-folder-navigation__heading">
      <span>{{ t('newcomerGuide.folders') }}</span>
      <small>{{ t('newcomerGuide.folderCount', { count: folders.length }) }}</small>
    </div>
    <ol v-if="folders.length" class="newcomer-folder-list">
      <li v-for="(folder, index) in folders" :key="folder._key || folder.id" class="newcomer-folder-list__item">
        <button
          class="newcomer-folder-entry"
          :class="{ 'is-active': index === activeIndex }"
          type="button"
          :aria-current="index === activeIndex ? 'page' : undefined"
          @click="$emit('select', index)"
        >
          <span class="newcomer-folder-entry__icon"><AppIcon name="folder" :size="19" /></span>
          <span class="newcomer-folder-entry__copy">
            <strong>{{ folder.title || t('newcomerGuide.editor.untitled') }}</strong>
            <small>{{ t('newcomerGuide.folderPosition', { current: index + 1, total: folders.length }) }}</small>
          </span>
          <AppIcon name="chevron-right" :size="16" />
        </button>
        <div v-if="editable" class="newcomer-folder-order" :aria-label="t('newcomerGuide.editor.folderActions', { title: folder.title || t('newcomerGuide.editor.untitled') })">
          <button type="button" :disabled="index === 0" :aria-label="t('newcomerGuide.editor.moveUp')" @click="$emit('move', index, -1)">↑</button>
          <button type="button" :disabled="index === folders.length - 1" :aria-label="t('newcomerGuide.editor.moveDown')" @click="$emit('move', index, 1)">↓</button>
          <button class="is-danger" type="button" :aria-label="t('newcomerGuide.editor.removeFolder', { title: folder.title || t('newcomerGuide.editor.untitled') })" @click="$emit('remove', index)">×</button>
        </div>
      </li>
    </ol>
    <p v-else class="muted newcomer-folder-empty">{{ t('newcomerGuide.emptyFolders') }}</p>
  </nav>
</template>
