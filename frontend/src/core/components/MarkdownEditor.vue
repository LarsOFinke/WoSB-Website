<script setup>
import { nextTick, ref } from 'vue'

import { useLocale } from '@/locales'

const props = defineProps({
  modelValue: { type: String, default: '' },
  rows: { type: Number, default: 8 },
  maxlength: { type: Number, default: 20000 },
  placeholder: { type: String, default: '' },
  required: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])
const { t } = useLocale()
const textarea = ref(null)

const tools = [
  { key: 'bold', label: 'B', title: 'markdown.toolbar.bold', before: '**', after: '**', fallback: t('markdown.placeholders.text') },
  { key: 'italic', label: 'I', title: 'markdown.toolbar.italic', before: '*', after: '*', fallback: t('markdown.placeholders.text') },
  { key: 'heading', label: 'H2', title: 'markdown.toolbar.heading', prefix: '## ' },
  { key: 'bulletList', label: '•', title: 'markdown.toolbar.bulletList', prefix: '- ' },
  { key: 'numberedList', label: '1.', title: 'markdown.toolbar.numberedList', prefix: '1. ' },
  { key: 'quote', label: '❯', title: 'markdown.toolbar.quote', prefix: '> ' },
  { key: 'link', label: '↗', title: 'markdown.toolbar.link', before: '[', after: '](https://)', fallback: t('markdown.placeholders.linkText') },
  { key: 'inlineCode', label: '</>', title: 'markdown.toolbar.inlineCode', before: '`', after: '`', fallback: t('markdown.placeholders.code') },
  { key: 'codeBlock', label: '{ }', title: 'markdown.toolbar.codeBlock', before: '```\n', after: '\n```', fallback: t('markdown.placeholders.code') },
]

function currentSelection() {
  const input = textarea.value
  const value = String(props.modelValue || '')
  return {
    input,
    value,
    start: input?.selectionStart ?? value.length,
    end: input?.selectionEnd ?? value.length,
  }
}

async function applyTool(tool) {
  const { input, value, start, end } = currentSelection()
  const selected = value.slice(start, end)
  let replacement = ''
  let selectionStart = start
  let selectionEnd = start

  if (tool.prefix) {
    const lineStart = value.lastIndexOf('\n', Math.max(start - 1, 0)) + 1
    const lineEndIndex = value.indexOf('\n', end)
    const lineEnd = lineEndIndex === -1 ? value.length : lineEndIndex
    const block = value.slice(lineStart, lineEnd)
    replacement = block.split('\n').map((line) => `${tool.prefix}${line}`).join('\n')
    emit('update:modelValue', `${value.slice(0, lineStart)}${replacement}${value.slice(lineEnd)}`)
    selectionStart = lineStart
    selectionEnd = lineStart + replacement.length
  } else {
    const content = selected || tool.fallback || ''
    replacement = `${tool.before || ''}${content}${tool.after || ''}`
    emit('update:modelValue', `${value.slice(0, start)}${replacement}${value.slice(end)}`)
    selectionStart = start + (tool.before || '').length
    selectionEnd = selectionStart + content.length
  }

  await nextTick()
  input?.focus()
  input?.setSelectionRange(selectionStart, selectionEnd)
}

async function insertToken(token) {
  const { input, value, start, end } = currentSelection()
  const before = value.slice(0, start)
  const after = value.slice(end)
  const prefix = before && !before.endsWith('\n') ? '\n\n' : ''
  const suffix = after && !after.startsWith('\n') ? '\n\n' : '\n\n'
  const insertion = `${prefix}${token}${suffix}`
  emit('update:modelValue', `${before}${insertion}${after}`)
  await nextTick()
  const cursor = before.length + insertion.length
  input?.focus()
  input?.setSelectionRange(cursor, cursor)
}

defineExpose({ insertToken, focus: () => textarea.value?.focus() })
</script>

<template>
  <div class="markdown-editor">
    <div class="markdown-toolbar" role="toolbar" :aria-label="t('markdown.toolbar.label')">
      <button
        v-for="tool in tools"
        :key="tool.key"
        class="markdown-tool-button"
        type="button"
        :title="t(tool.title)"
        :aria-label="t(tool.title)"
        @click="applyTool(tool)"
      >
        {{ tool.label }}
      </button>
      <span class="markdown-toolbar-hint">{{ t('markdown.toolbar.hint') }}</span>
    </div>
    <label class="input-panel embedded-field textarea-shell markdown-textarea-shell">
      <textarea
        ref="textarea"
        :value="modelValue"
        :rows="rows"
        :maxlength="maxlength"
        :placeholder="placeholder"
        :required="required"
        @input="emit('update:modelValue', $event.target.value)"
      ></textarea>
    </label>
  </div>
</template>
