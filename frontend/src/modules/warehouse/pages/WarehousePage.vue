<script setup>
import WarehouseEntryEditor from '@/modules/warehouse/components/WarehouseEntryEditor.vue'
import { useWarehousePage } from '@/modules/warehouse/composables/useWarehousePage'
import '@/modules/warehouse/styles/warehouse.css'

const {
  t, canManageWarehouse, page, fleets, members, ports, resources, assignments, assignmentFleetId, assignmentOverlayOpen, loading, saving, publishingOverview, error, success,
  editorOpen, editorTitle, draft, filters, formatAmount, formatDateTime, pageStart, pageEnd, hasPreviousPage, hasNextPage,
  loadEntries, previousPage, nextPage, openCreate, openEdit, closeEditor, changeDraftFleet, saveEntry, removeEntry,
  clearFilters, openAssignmentOverlay, closeAssignmentOverlay, loadAssignments, saveAssignment, publishOverview,
} = useWarehousePage()
</script>

<template>
  <section class="warehouse-page" aria-labelledby="warehouse-title">
    <header class="warehouse-hero">
      <div>
        <p class="eyebrow">{{ t('warehouse.eyebrow') }}</p>
        <h1 id="warehouse-title">{{ t('warehouse.title') }}</h1>
        <p>{{ t('warehouse.subtitle') }}</p>
      </div>
      <div class="warehouse-hero-actions">
        <button class="button-box" type="button" :disabled="loading" @click="loadEntries">{{ t('warehouse.actions.refresh') }}</button>
        <button v-if="canManageWarehouse" class="button-box" type="button" :disabled="publishingOverview" @click="publishOverview()">{{ publishingOverview ? t('warehouse.actions.publishingOverview') : t('warehouse.actions.publishOverview') }}</button>
        <button v-if="canManageWarehouse" class="button-box primary-action" type="button" @click="openCreate">{{ t('warehouse.actions.add') }}</button>
      </div>
    </header>

    <div class="warehouse-workspace">
      <section class="warehouse-filters wire-section" :aria-label="t('warehouse.filters.title')">
        <header>
          <div><h2>{{ t('warehouse.filters.title') }}</h2><p>{{ t('warehouse.filters.hint') }}</p></div>
          <button class="small-action" type="button" @click="clearFilters">{{ t('warehouse.actions.clearFilters') }}</button>
        </header>
        <div class="warehouse-filter-grid">
          <label><span>{{ t('warehouse.fields.fleet') }}</span><select v-model="filters.fleet_id" @change="loadEntries({ resetOffset: true })"><option value="">{{ t('warehouse.filters.all') }}</option><option v-for="fleet in fleets" :key="fleet.id" :value="fleet.id">{{ fleet.name }}</option></select></label>
          <label><span>{{ t('warehouse.fields.holder') }}</span><select v-model="filters.holder" @change="loadEntries({ resetOffset: true })"><option value="">{{ t('warehouse.filters.all') }}</option><option v-for="holder in page.holders" :key="holder" :value="holder">{{ holder }}</option></select></label>
          <label><span>{{ t('warehouse.fields.port') }}</span><select v-model="filters.port" @change="loadEntries({ resetOffset: true })"><option value="">{{ t('warehouse.filters.all') }}</option><option v-for="port in ports" :key="port.id" :value="port.name">{{ port.name }}</option></select></label>
          <label><span>{{ t('warehouse.fields.resource') }}</span><select v-model="filters.resource" @change="loadEntries({ resetOffset: true })"><option value="">{{ t('warehouse.filters.all') }}</option><option v-for="resource in resources" :key="resource" :value="resource">{{ resource }}</option></select></label>
          <label><span>{{ t('warehouse.fields.status') }}</span><select v-model="filters.reserved" @change="loadEntries({ resetOffset: true })"><option value="">{{ t('warehouse.filters.all') }}</option><option value="false">{{ t('warehouse.status.available') }}</option><option value="true">{{ t('warehouse.status.reserved') }}</option></select></label>
          <label><span>{{ t('warehouse.fields.collectionStatus') }}</span><select v-model="filters.collection_status" @change="loadEntries({ resetOffset: true })"><option value="">{{ t('warehouse.filters.all') }}</option><option value="up_for_collection">{{ t('warehouse.status.upForCollection') }}</option><option value="in_warehouse">{{ t('warehouse.status.inWarehouse') }}</option></select></label>
        </div>
      </section>

      <section v-if="canManageWarehouse" class="warehouse-assignment-launch wire-section">
        <div><h2>{{ t('warehouse.assignments.title') }}</h2><p>{{ t('warehouse.assignments.hint') }}</p></div>
        <button class="button-box" type="button" @click="openAssignmentOverlay">{{ t('warehouse.assignments.open') }}</button>
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
        <div v-else-if="!page.items.length" class="warehouse-empty"><strong>{{ t('warehouse.ledger.emptyTitle') }}</strong><p>{{ t('warehouse.ledger.emptyText') }}</p><button v-if="canManageWarehouse" class="button-box" type="button" @click="openCreate">{{ t('warehouse.actions.add') }}</button></div>
        <div v-else class="warehouse-table-shell" tabindex="0" :aria-label="t('warehouse.ledger.tableLabel')">
          <table class="warehouse-table">
            <thead><tr><th>{{ t('warehouse.fields.holder') }}</th><th>{{ t('warehouse.fields.fleet') }}</th><th>{{ t('warehouse.fields.port') }}</th><th>{{ t('warehouse.fields.resource') }}</th><th>{{ t('warehouse.fields.amount') }}</th><th>{{ t('warehouse.fields.collectionStatus') }}</th><th>{{ t('warehouse.fields.status') }}</th><th>{{ t('warehouse.fields.updated') }}</th><th v-if="canManageWarehouse"><span class="sr-only">{{ t('warehouse.fields.actions') }}</span></th></tr></thead>
            <tbody>
              <tr v-for="entry in page.items" :key="entry.id">
                <td><strong>{{ entry.holder_name }}</strong><small>{{ entry.member_user_id ? t('warehouse.holder.linked') : t('warehouse.holder.custom') }}</small></td>
                <td>{{ entry.fleet_name }}</td><td>{{ entry.port }}<small v-if="entry.port_assignee_name">{{ t('warehouse.fields.pickupAssignee') }}: {{ entry.port_assignee_name }}</small></td><td>{{ entry.resource }}</td>
                <td class="warehouse-amount">{{ formatAmount(entry.amount) }}</td>
                <td><span class="warehouse-status" :class="entry.collection_status === 'in_warehouse' ? 'is-available' : 'is-reserved'">{{ entry.collection_status === 'in_warehouse' ? t('warehouse.status.inWarehouse') : t('warehouse.status.upForCollection') }}</span></td>
                <td><span class="warehouse-status" :class="entry.reserved ? 'is-reserved' : 'is-available'">{{ entry.reserved ? t('warehouse.status.reserved') : t('warehouse.status.available') }}</span></td>
                <td><span>{{ formatDateTime(entry.updated_at) }}</span><small>{{ entry.updated_by || '—' }}</small></td>
                <td v-if="canManageWarehouse"><div class="warehouse-row-actions"><button class="small-action" type="button" @click="openEdit(entry)">{{ t('warehouse.actions.edit') }}</button><button class="small-action danger" type="button" @click="removeEntry(entry)">{{ t('warehouse.actions.delete') }}</button></div></td>
              </tr>
            </tbody>
          </table>
        </div>
        <footer v-if="page.total" class="warehouse-pagination" aria-label="Warehouse pages">
          <span>{{ pageStart }}–{{ pageEnd }} / {{ page.total }}</span>
          <div><button class="small-action" type="button" :disabled="!hasPreviousPage || loading" @click="previousPage">{{ t('common.previous') }}</button><button class="small-action" type="button" :disabled="!hasNextPage || loading" @click="nextPage">{{ t('common.next') }}</button></div>
        </footer>
      </section>
    </div>

    <WarehouseEntryEditor v-if="canManageWarehouse && editorOpen" :title="editorTitle" :draft="draft" :fleets="fleets" :members="members" :ports="ports" :resources="resources" :saving="saving" :t="t" @cancel="closeEditor" @fleet-change="changeDraftFleet" @save="saveEntry" />

    <div v-if="canManageWarehouse && assignmentOverlayOpen" class="warehouse-editor-backdrop" @click.self="closeAssignmentOverlay">
      <section class="warehouse-editor warehouse-assignment-overlay" role="dialog" aria-modal="true" :aria-labelledby="'warehouse-assignment-title'">
        <header class="warehouse-editor__header">
          <div><p class="eyebrow">{{ t('warehouse.assignments.eyebrow') }}</p><h2 id="warehouse-assignment-title">{{ t('warehouse.assignments.title') }}</h2></div>
          <button class="small-action" type="button" :aria-label="t('common.close')" @click="closeAssignmentOverlay">×</button>
        </header>
        <p class="warehouse-overlay-hint">{{ t('warehouse.assignments.hint') }}</p>
        <label class="input-panel"><span>{{ t('warehouse.fields.fleet') }}</span><select v-model="assignmentFleetId" @change="loadAssignments()"><option v-for="fleet in fleets" :key="fleet.id" :value="fleet.id">{{ fleet.name }}</option></select></label>
        <div class="warehouse-assignment-grid">
          <label v-for="assignment in assignments" :key="assignment.port_id" class="input-panel"><span>{{ assignment.port_name }}</span><select :value="assignment.assignee_user_id || ''" @change="saveAssignment(assignment, $event)"><option value="">{{ t('warehouse.assignments.unassigned') }}</option><option v-for="member in members" :key="member.id" :value="member.id">{{ member.display_name }}</option></select></label>
        </div>
        <footer class="warehouse-editor__actions"><button class="button-box" type="button" @click="closeAssignmentOverlay">{{ t('common.close') }}</button></footer>
      </section>
    </div>
  </section>
</template>
