<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { filterOptionGroups } from '@/modules/builds/domain/optionSearch'
import { calculatePickerPlacement } from '@/modules/builds/domain/pickerPlacement'

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  options: { type: Array, default: () => [] },
  groups: { type: Array, default: () => [] },
  placeholder: { type: String, default: '' },
  ariaLabel: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  allowEmpty: { type: Boolean, default: true },
  searchable: { type: Boolean, default: false },
  searchPlaceholder: { type: String, default: '' },
  noResultsText: { type: String, default: '' },
  required: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])
const root = ref(null)
const menu = ref(null)
const open = ref(false)
const activeIndex = ref(-1)
const searchQuery = ref('')
const searchInput = ref(null)
const menuStyle = ref({})
let positionFrame = 0

const normalizedGroups = computed(() => {
  if (props.groups.length) return props.groups
  return [{ key: 'default', label: '', options: props.options }]
})
const filteredGroups = computed(() => filterOptionGroups(normalizedGroups.value, searchQuery.value))
const flatOptions = computed(() => normalizedGroups.value.flatMap((group) => group.options || []))
const filteredOptions = computed(() => filteredGroups.value.flatMap((group) => group.options || []))
const selected = computed(() => flatOptions.value.find((option) => option.value === props.modelValue) || null)
const enabledOptions = computed(() => filteredOptions.value.filter((option) => !option.disabled))

function updateMenuPosition() {
  if (!open.value || !root.value) return
  if (window.matchMedia('(max-width: 720px)').matches) {
    menuStyle.value = {}
    return
  }
  const trigger = root.value.querySelector('.build-option-picker-trigger')
  if (!trigger) return
  const placement = calculatePickerPlacement(trigger.getBoundingClientRect(), {
    width: window.visualViewport?.width || window.innerWidth,
    height: window.visualViewport?.height || window.innerHeight,
  })
  menuStyle.value = {
    left: `${placement.left}px`,
    width: `${placement.width}px`,
    maxHeight: `${placement.maxHeight}px`,
    top: placement.top == null ? 'auto' : `${placement.top}px`,
    bottom: placement.bottom == null ? 'auto' : `${placement.bottom}px`,
  }
}

function scheduleMenuPosition() {
  if (!open.value) return
  if (positionFrame) window.cancelAnimationFrame(positionFrame)
  positionFrame = window.requestAnimationFrame(() => {
    positionFrame = 0
    updateMenuPosition()
  })
}

function openMenu() {
  if (props.disabled) return
  open.value = true
  const selectedIndex = enabledOptions.value.findIndex((option) => option.value === props.modelValue)
  activeIndex.value = selectedIndex >= 0 ? selectedIndex : 0
  searchQuery.value = ''
  nextTick(() => {
    updateMenuPosition()
    if (props.searchable) searchInput.value?.focus({ preventScroll: true })
    else menu.value?.focus({ preventScroll: true })
  })
}

function closeMenu({ restoreFocus = false } = {}) {
  open.value = false
  searchQuery.value = ''
  menuStyle.value = {}
  if (positionFrame) {
    window.cancelAnimationFrame(positionFrame)
    positionFrame = 0
  }
  if (restoreFocus) root.value?.querySelector('.build-option-picker-trigger')?.focus()
}

function toggleMenu() {
  if (open.value) closeMenu()
  else openMenu()
}

function selectValue(value) {
  emit('update:modelValue', value)
  closeMenu({ restoreFocus: true })
}

function moveActive(delta) {
  if (!enabledOptions.value.length) return
  const next = (activeIndex.value + delta + enabledOptions.value.length) % enabledOptions.value.length
  activeIndex.value = next
  const value = enabledOptions.value[next]?.value
  nextTick(() => menu.value?.querySelector(`[data-option-value="${CSS.escape(String(value))}"]`)?.scrollIntoView({ block: 'nearest' }))
}

function onTriggerKeydown(event) {
  if (props.disabled) return
  if (['ArrowDown', 'ArrowUp'].includes(event.key)) {
    event.preventDefault()
    if (!open.value) openMenu()
    else moveActive(event.key === 'ArrowDown' ? 1 : -1)
    return
  }
  if (event.key === 'Escape' && open.value) {
    event.preventDefault()
    closeMenu()
  }
}

function onMenuKeydown(event) {
  const fromSearch = event.target === searchInput.value
  if (fromSearch && !['ArrowDown', 'ArrowUp', 'Escape', 'Tab'].includes(event.key)) return
  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault()
    moveActive(event.key === 'ArrowDown' ? 1 : -1)
  } else if (event.key === 'Home') {
    event.preventDefault()
    activeIndex.value = 0
  } else if (event.key === 'End') {
    event.preventDefault()
    activeIndex.value = Math.max(0, enabledOptions.value.length - 1)
  } else if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    const option = enabledOptions.value[activeIndex.value]
    if (option) selectValue(option.value)
  } else if (event.key === 'Escape' || event.key === 'Tab') {
    closeMenu({ restoreFocus: event.key === 'Escape' })
  }
}

function onDocumentPointerDown(event) {
  if (!open.value) return
  if (root.value?.contains(event.target) || menu.value?.contains(event.target)) return
  closeMenu()
}

watch(searchQuery, () => { activeIndex.value = enabledOptions.value.length ? 0 : -1 })
watch(() => [props.options, props.groups], () => nextTick(scheduleMenuPosition), { deep: true })

onMounted(() => {
  document.addEventListener('pointerdown', onDocumentPointerDown)
  window.addEventListener('resize', scheduleMenuPosition)
  window.addEventListener('scroll', scheduleMenuPosition, true)
  window.visualViewport?.addEventListener('resize', scheduleMenuPosition)
  window.visualViewport?.addEventListener('scroll', scheduleMenuPosition)
})
onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onDocumentPointerDown)
  window.removeEventListener('resize', scheduleMenuPosition)
  window.removeEventListener('scroll', scheduleMenuPosition, true)
  window.visualViewport?.removeEventListener('resize', scheduleMenuPosition)
  window.visualViewport?.removeEventListener('scroll', scheduleMenuPosition)
  if (positionFrame) window.cancelAnimationFrame(positionFrame)
})
</script>

<template>
  <div ref="root" class="build-option-picker" :class="{ 'is-open': open, 'is-disabled': disabled }">
    <button
      type="button"
      class="build-option-picker-trigger"
      role="combobox"
      aria-haspopup="listbox"
      :aria-expanded="open"
      :aria-label="ariaLabel"
      :aria-required="required || undefined"
      :disabled="disabled"
      @click="toggleMenu"
      @keydown="onTriggerKeydown"
    >
      <span class="build-option-picker-trigger-copy">
        <strong>{{ selected?.label || placeholder }}</strong>
        <small v-if="selected?.meta">{{ selected.meta }}</small>
      </span>
      <span class="build-option-picker-chevron" aria-hidden="true">⌄</span>
    </button>

    <Teleport to="body">
      <div
        v-if="open"
        ref="menu"
        class="build-option-picker-menu"
        role="listbox"
        tabindex="-1"
        :aria-label="ariaLabel"
        :style="menuStyle"
        @keydown="onMenuKeydown"
      >
        <label v-if="searchable" class="build-option-picker-search">
          <span class="sr-only">{{ searchPlaceholder }}</span>
          <input
            ref="searchInput"
            v-model="searchQuery"
            type="search"
            autocomplete="off"
            :placeholder="searchPlaceholder"
            @keydown.stop="onMenuKeydown"
          />
        </label>
        <button
          v-if="allowEmpty"
          type="button"
          class="build-option-picker-option is-empty"
          role="option"
          :aria-selected="modelValue === ''"
          @click="selectValue('')"
        >
          <span class="build-option-picker-option-copy"><strong>{{ placeholder }}</strong></span>
        </button>

        <p v-if="searchable && filteredGroups.length === 0" class="build-option-picker-empty">{{ noResultsText }}</p>

        <section v-for="group in filteredGroups" :key="group.key" class="build-option-picker-group">
          <p v-if="group.label" class="build-option-picker-group-label">{{ group.label }}</p>
          <button
            v-for="option in group.options"
            :key="option.value"
            type="button"
            class="build-option-picker-option"
            :class="{ 'is-selected': option.value === modelValue, 'is-active': enabledOptions[activeIndex]?.value === option.value }"
            role="option"
            :data-option-value="option.value"
            :aria-selected="option.value === modelValue"
            :disabled="option.disabled"
            @mouseenter="activeIndex = enabledOptions.findIndex((candidate) => candidate.value === option.value)"
            @click="selectValue(option.value)"
          >
            <img v-if="option.image" :src="option.image" alt="" />
            <span class="build-option-picker-option-copy">
              <strong>{{ option.label }}</strong>
              <small v-if="option.meta">{{ option.meta }}</small>
            </span>
            <span v-if="option.value === modelValue" class="build-option-picker-check" aria-hidden="true">✓</span>
          </button>
        </section>
      </div>
    </Teleport>
  </div>
</template>
