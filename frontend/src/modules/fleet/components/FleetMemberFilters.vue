<script setup>
import AppIcon from '@/core/components/AppIcon.vue'
import { useLocale } from '@/locales'

defineProps({
  search: { type: String, default: '' },
  status: { type: String, default: '' },
  role: { type: String, default: '' },
  statuses: { type: Array, required: true },
  roles: { type: Array, required: true },
})

const emit = defineEmits(['update:search', 'update:status', 'update:role'])
const { t } = useLocale()
</script>

<template>
  <div class="fleet-refresh-filters">
    <label class="fleet-refresh-filter fleet-refresh-search">
      <AppIcon name="compass" :size="18" />
      <input :value="search" type="search" :placeholder="t('fleets.manage.memberSearchPlaceholder')" @input="emit('update:search', $event.target.value)" />
    </label>
    <label class="fleet-refresh-filter">
      <span>{{ t('fleets.manage.statusFilter') }}</span>
      <select :value="status" @change="emit('update:status', $event.target.value)">
        <option value="">{{ t('fleets.manage.allStatuses') }}</option>
        <option v-for="item in statuses" :key="item" :value="item">{{ t(`fleets.status.${item}`) }}</option>
      </select>
    </label>
    <label class="fleet-refresh-filter">
      <span>{{ t('fleets.manage.roleFilter') }}</span>
      <select :value="role" @change="emit('update:role', $event.target.value)">
        <option value="">{{ t('fleets.manage.allRoles') }}</option>
        <option v-for="item in roles" :key="item.code" :value="item.code">{{ item.label }}</option>
      </select>
    </label>
  </div>
</template>
