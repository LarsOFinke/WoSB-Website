<script setup>
import { onBeforeUnmount, onMounted } from 'vue'

import PageHeader from '@/core/components/PageHeader.vue'
import StaffWorkspaceNavigation from '@/modules/admin/components/StaffWorkspaceNavigation.vue'
import '@/modules/admin/styles/staffWorkspace.css'

defineProps({
  eyebrow: { type: String, default: '' },
  title: { type: String, required: true },
  description: { type: String, default: '' },
  titleId: { type: String, default: '' },
  groups: { type: Array, default: () => [] },
  activeKey: { type: String, default: '' },
  user: { type: Object, default: null },
  roleLabel: { type: String, default: '' },
  status: { type: String, default: '' },
  isAdmin: { type: Boolean, default: false },
})

let restoreExpandedSidebar = false

onMounted(() => {
  if (typeof document === 'undefined') return
  restoreExpandedSidebar = !document.body.classList.contains('sidebar-collapsed')
  document.body.classList.add('sidebar-collapsed', 'staff-workspace-route')
})

onBeforeUnmount(() => {
  if (typeof document === 'undefined') return
  document.body.classList.remove('staff-workspace-route')
  if (restoreExpandedSidebar) document.body.classList.remove('sidebar-collapsed')
})
</script>

<template>
  <section class="staff-workspace-page" :aria-labelledby="titleId || undefined">
    <div class="staff-workspace-shell">
      <PageHeader :eyebrow="eyebrow" :title="title" :description="description" :title-id="titleId">
        <template #meta>
          <span v-if="user" class="staff-identity-line"><strong>{{ user.display_name }}</strong><span>{{ roleLabel }}</span></span>
          <span v-if="status" class="staff-service-status"><i aria-hidden="true"></i>{{ status }}</span>
        </template>
        <template v-if="$slots.actions" #actions><slot name="actions" /></template>
      </PageHeader>

      <div class="staff-workspace-layout">
        <StaffWorkspaceNavigation :groups="groups" :active-key="activeKey" :is-admin="isAdmin" />
        <div class="staff-workspace-main"><slot /></div>
      </div>
    </div>
  </section>
</template>
