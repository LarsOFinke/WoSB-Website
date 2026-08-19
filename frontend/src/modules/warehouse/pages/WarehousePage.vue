<script setup>
import StaffWorkspaceShell from '@/modules/admin/components/StaffWorkspaceShell.vue'
import WarehouseEntryEditor from '@/modules/warehouse/components/WarehouseEntryEditor.vue'
import { useWarehousePage } from '@/modules/warehouse/composables/useWarehousePage'
import '@/modules/warehouse/styles/warehouse.css'

const {
  t, isAdmin, user, navigationGroups, page, fleets, members, loading, saving, error, success,
  editorOpen, editorTitle, draft, filters, formatAmount, formatDateTime, loadEntries, openCreate,
  openEdit, closeEditor, changeDraftFleet, saveEntry, removeEntry, clearFilters,
} = useWarehousePage()
</script>

<template>
  <StaffWorkspaceShell
    :eyebrow="t('warehouse.eyebrow')"
    :title="t('warehouse.title')"
    :description="t('warehouse.subtitle')"
    title-id="warehouse-title"
    :groups="navigationGroups"
    active-key="warehouse"
    :user="user"
    :role-label="user ? t(`roles.${user.role}`) : ''"
    :is-admin="isAdmin"
  >
    <template #actions>
      <button class="button-box" type="button" :disabled="loading" @click="loadEntries">{{ t('warehouse.actions.refresh') }}</button>
      <button class="button-box primary-action" type="button" @click="openCreate">{{ t('warehouse.actions.add') }}</button>
    </template>

    <div class="warehouse-workspace staff-subworkspace">
      <section class="warehouse-filters wire-section" :aria-label="t('warehouse.filters.title')">
        <header>
          <div><h2>{{ t('warehouse.filters.title') }}</h2><p>{{ t('warehouse.filters.hint') }}</p></div>
          <button class="small-action" type="button" @click="clearFilters">{{ t('warehouse.actions.clearFilters') }}</button>
        </header>
        <div class="warehouse-filter-grid">
          <label><span>{{ t('warehouse.fields.fleet') }}</span><select v-model="filters.fleet_id" @change="loadEntries"><option value="">{{ t('warehouse.filters.all') }}</option><option v-for="fleet in fleets" :key="fleet.id" :value="fleet.id">{{ fleet.name }}</option></select></label>
          <label><span>{{ t('warehouse.fields.holder') }}</span><select v-model="filters.holder" @change="loadEntries"><option value="">{{ t('warehouse.filters.all') }}</option><option v-for="holder in page.holders" :key="holder" :value="holder">{{ holder }}</option></select></label>
          <label><span>{{ t('warehouse.fields.port') }}</span><select v-model="filters.port" @change="loadEntries"><option value="">{{ t('warehouse.filters.all') }}</option><option v-for="port in page.ports" :key="port" :value="port">{{ port }}</option></select></label>
          <label><span>{{ t('warehouse.fields.resource') }}</span><select v-model="filters.resource" @change="loadEntries"><option value="">{{ t('warehouse.filters.all') }}</option><option v-for="resource in page.resources" :key="resource" :value="resource">{{ resource }}</option></select></label>
          <label><span>{{ t('warehouse.fields.status') }}</span><select v-model="filters.reserved" @change="loadEntries"><option value="">{{ t('warehouse.filters.all') }}</option><option value="false">{{ t('warehouse.status.available') }}</option><option value="true">{{ t('warehouse.status.reserved') }}</option></select></label>
        </div>
      </section>

      <section class="warehouse-summary-grid" aria-live="polite">
        <article><span>{{ t('warehouse.summary.matchingStock') }}</span><strong>{{ formatAmount(page.matching_stock) }}</strong><small>{{ t('warehouse.summary.stockHint') }}</small></article>
        <article><span>{{ t('warehouse.summary.reserved') }}</span><strong>{{ formatAmount(page.reserved_stock) }}</strong><small>{{ t('warehouse.summary.reservedHint') }}</small></article>
        <article><span>{{ t('warehouse.summary.available') }}</span><strong>{{ formatAmount(page.available_stock) }}</strong><small>{{ t('warehouse.summary.availableHint') }}</small></article>
        <article><span>{{ t('warehouse.summary.rows') }}</span><strong>{{ formatAmount(page.total) }}</strong><small>{{ t('warehouse.summary.rowsHint') }}</small></article>
      </section>

      <p v-if="success" class="success-text warehouse-message" role="status">{{ success }}</p>
      <p v-if="error" class="error-text warehouse-message" role="alert">{{ error }}</p>

      <section class="warehouse-ledger wire-section">
        <header><div><h2>{{ t('warehouse.ledger.title') }}</h2><p>{{ t('warehouse.ledger.hint') }}</p></div><span class="summary-pill">{{ page.total }}</span></header>
        <div v-if="loading" class="table-state">{{ t('warehouse.actions.loading') }}</div>
        <div v-else-if="!page.items.length" class="warehouse-empty"><strong>{{ t('warehouse.ledger.emptyTitle') }}</strong><p>{{ t('warehouse.ledger.emptyText') }}</p><button class="button-box" type="button" @click="openCreate">{{ t('warehouse.actions.add') }}</button></div>
        <div v-else class="warehouse-table-shell" tabindex="0" :aria-label="t('warehouse.ledger.tableLabel')">
          <table class="warehouse-table">
            <thead><tr><th>{{ t('warehouse.fields.holder') }}</th><th>{{ t('warehouse.fields.fleet') }}</th><th>{{ t('warehouse.fields.port') }}</th><th>{{ t('warehouse.fields.resource') }}</th><th>{{ t('warehouse.fields.amount') }}</th><th>{{ t('warehouse.fields.status') }}</th><th>{{ t('warehouse.fields.updated') }}</th><th><span class="sr-only">{{ t('warehouse.fields.actions') }}</span></th></tr></thead>
            <tbody>
              <tr v-for="entry in page.items" :key="entry.id">
                <td><strong>{{ entry.holder_name }}</strong><small>{{ entry.member_user_id ? t('warehouse.holder.linked') : t('warehouse.holder.custom') }}</small></td>
                <td>{{ entry.fleet_name }}</td><td>{{ entry.port }}</td><td>{{ entry.resource }}</td>
                <td class="warehouse-amount">{{ formatAmount(entry.amount) }}</td>
                <td><span class="warehouse-status" :class="entry.reserved ? 'is-reserved' : 'is-available'">{{ entry.reserved ? t('warehouse.status.reserved') : t('warehouse.status.available') }}</span></td>
                <td><span>{{ formatDateTime(entry.updated_at) }}</span><small>{{ entry.updated_by || '—' }}</small></td>
                <td><div class="warehouse-row-actions"><button class="small-action" type="button" @click="openEdit(entry)">{{ t('warehouse.actions.edit') }}</button><button class="small-action danger" type="button" @click="removeEntry(entry)">{{ t('warehouse.actions.delete') }}</button></div></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>

    <WarehouseEntryEditor v-if="editorOpen" :title="editorTitle" :draft="draft" :fleets="fleets" :members="members" :saving="saving" :t="t" @cancel="closeEditor" @fleet-change="changeDraftFleet" @save="saveEntry" />
  </StaffWorkspaceShell>
</template>
