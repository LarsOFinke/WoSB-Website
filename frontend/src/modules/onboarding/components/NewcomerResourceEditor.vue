<script setup>
import { useLocale } from '@/locales'

const props = defineProps({
  resource: { type: Object, required: true },
  resourceIndex: { type: Number, required: true },
  resourceCount: { type: Number, required: true },
  guides: { type: Array, default: () => [] },
  builds: { type: Array, default: () => [] },
  resourceTypeOptions: { type: Array, default: () => [] },
  resourceOptionsLoading: { type: Boolean, default: false },
})

defineEmits(['remove', 'move', 'type-change'])
const { t } = useLocale()
const initiallyOpen = !props.resource.resource_id && !props.resource.url
</script>

<template>
  <details class="newcomer-resource-editor-row" :open="initiallyOpen">
    <summary>
      <span class="newcomer-resource-editor-index">{{ String(resourceIndex + 1).padStart(2, '0') }}</span>
      <span>
        <strong>{{ resource.label || t('newcomerGuide.editor.resource', { index: resourceIndex + 1 }) }}</strong>
        <small>{{ t(`newcomerGuide.editor.types.${resource.resource_type}`) }}</small>
      </span>
    </summary>
    <div class="newcomer-resource-editor-body">
      <div class="newcomer-resource-editor-actions compact-actions">
        <button type="button" :disabled="resourceIndex === 0" :aria-label="t('newcomerGuide.editor.moveUp')" @click="$emit('move', resourceIndex, -1)">↑</button>
        <button type="button" :disabled="resourceIndex === resourceCount - 1" :aria-label="t('newcomerGuide.editor.moveDown')" @click="$emit('move', resourceIndex, 1)">↓</button>
        <button class="is-danger" type="button" @click="$emit('remove', resourceIndex)">{{ t('common.remove') }}</button>
      </div>

      <div class="directory-form-grid">
        <label class="input-panel embedded-field">
          <span>{{ t('common.type') }}</span>
          <select v-model="resource.resource_type" @change="$emit('type-change', resource)">
            <option v-for="entry in resourceTypeOptions" :key="entry.value" :value="entry.value">{{ entry.label }}</option>
          </select>
        </label>
        <label v-if="resource.resource_type === 'guide'" class="input-panel embedded-field">
          <span>{{ t('common.guides') }}</span>
          <select v-model="resource.resource_id" required :disabled="resourceOptionsLoading">
            <option :value="null">{{ guides.length ? t('common.empty') : t('newcomerGuide.editor.noGuides') }}</option>
            <option v-for="guide in guides" :key="guide.id" :value="guide.id">{{ guide.title }}</option>
          </select>
        </label>
        <label v-else-if="resource.resource_type === 'build'" class="input-panel embedded-field">
          <span>{{ t('common.builds') }}</span>
          <select v-model="resource.resource_id" required :disabled="resourceOptionsLoading">
            <option :value="null">{{ builds.length ? t('common.empty') : t('newcomerGuide.editor.noBuilds') }}</option>
            <option v-for="build in builds" :key="build.id" :value="build.id">{{ build.build_name }}</option>
          </select>
        </label>
        <label v-else class="input-panel embedded-field">
          <span>{{ t('newcomerGuide.editor.url') }}</span>
          <input v-model="resource.url" maxlength="500" required :placeholder="resource.resource_type === 'internal' ? '/guides' : 'https://…'" />
        </label>
        <label class="input-panel embedded-field">
          <span>{{ t('newcomerGuide.editor.customLabel') }}</span>
          <input v-model="resource.label" maxlength="180" :placeholder="t('newcomerGuide.editor.customLabelHint')" />
        </label>
      </div>
      <label class="input-panel embedded-field">
        <span>{{ t('common.description') }}</span>
        <textarea v-model="resource.description" rows="2" maxlength="500" />
      </label>
    </div>
  </details>
</template>
