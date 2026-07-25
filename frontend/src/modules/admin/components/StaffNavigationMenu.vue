<script setup>
import AppIcon from '@/core/components/AppIcon.vue'
import { useLocale } from '@/locales'

const { t } = useLocale()

defineProps({
  groups: { type: Array, default: () => [] },
  activeKey: { type: String, default: '' },
})

defineEmits(['navigate'])
</script>

<template>
  <nav class="staff-navigation-menu" :aria-label="t('admin.tabsLabel')">
    <section v-for="group in groups" :key="group.key" class="staff-navigation-group">
      <span class="staff-navigation-group-label">{{ group.label }}</span>
      <RouterLink
        v-for="item in group.items"
        :key="item.key"
        class="staff-navigation-link"
        :class="{ 'is-active': activeKey === item.key, 'is-protected': item.protected }"
        :to="item.to"
        :aria-current="activeKey === item.key ? 'page' : undefined"
        @click="$emit('navigate', item)"
      >
        <AppIcon :name="item.icon" :size="18" />
        <span>{{ item.label }}</span>
        <AppIcon v-if="item.protected" class="staff-navigation-lock" name="lock" :size="13" />
        <AppIcon v-else class="staff-navigation-arrow" name="chevron-right" :size="14" />
      </RouterLink>
    </section>
  </nav>
</template>
