import { computed, onMounted, reactive, ref } from 'vue'

import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import {
  createWarehouseEntry,
  deleteWarehouseEntry,
  listWarehouseEntries,
  listWarehouseFleets,
  listWarehouseMembers,
  listWarehousePortAssignments,
  listWarehousePorts,
  listWarehouseResources,
  publishWarehouseOverviewWebhook,
  updateWarehouseEntry,
  updateWarehousePortAssignment,
} from '@/modules/warehouse/api/warehouse'
import {
  createWarehouseDraft,
  formatWarehouseAmount,
  warehouseDraftFromEntry,
  warehouseDraftIssue,
  warehousePayload,
} from '@/modules/warehouse/domain/warehouse'

const EMPTY_PAGE = {
  items: [], total: 0, matching_stock: 0, reserved_stock: 0, available_stock: 0,
  holders: [], ports: [], resources: [],
}

export function useWarehousePage() {
  const { locale, t } = useLocale()
  const { isStaff } = useSession()
  const canManageWarehouse = computed(() => isStaff.value)
  const page = ref({ ...EMPTY_PAGE })
  const fleets = ref([])
  const members = ref([])
  const ports = ref([])
  const resources = ref([])
  const assignments = ref([])
  const assignmentFleetId = ref('')
  const assignmentOverlayOpen = ref(false)
  const loading = ref(false)
  const saving = ref(false)
  const error = ref('')
  const success = ref('')
  const publishingOverview = ref(false)
  const editorOpen = ref(false)
  const editingId = ref(null)
  const draft = reactive(createWarehouseDraft())
  const filters = reactive({ fleet_id: '', holder: '', port: '', resource: '', reserved: '', collection_status: '' })
  const pageSize = 100
  const offset = ref(0)
  let loadSequence = 0

  const editorTitle = computed(() => editingId.value
    ? t('warehouse.editor.editTitle')
    : t('warehouse.editor.createTitle'))
  const formatAmount = (value) => formatWarehouseAmount(value, locale.value)
  const formatDateTime = (value) => value ? new Date(value).toLocaleString(locale.value) : '—'
  const pageStart = computed(() => page.value.total ? offset.value + 1 : 0)
  const pageEnd = computed(() => Math.min(offset.value + page.value.items.length, page.value.total))
  const hasPreviousPage = computed(() => offset.value > 0)
  const hasNextPage = computed(() => offset.value + page.value.items.length < page.value.total)

  async function loadEntries({ resetOffset = false } = {}) {
    if (resetOffset) offset.value = 0
    const sequence = ++loadSequence
    loading.value = true
    error.value = ''
    try {
      const result = await listWarehouseEntries({
        fleet_id: filters.fleet_id,
        holder: filters.holder,
        port: filters.port,
        resource: filters.resource,
        reserved: filters.reserved,
        collection_status: filters.collection_status,
        limit: pageSize,
        offset: offset.value,
      })
      if (sequence === loadSequence) page.value = result
    } catch (err) {
      if (sequence === loadSequence) error.value = err.message || t('warehouse.errors.load')
    } finally {
      if (sequence === loadSequence) loading.value = false
    }
  }

  function previousPage() {
    if (!hasPreviousPage.value) return
    offset.value = Math.max(0, offset.value - pageSize)
    loadEntries()
  }

  function nextPage() {
    if (!hasNextPage.value) return
    offset.value += pageSize
    loadEntries()
  }

  async function loadMembers(fleetId) {
    members.value = []
    if (!fleetId) return
    try {
      members.value = await listWarehouseMembers(fleetId)
    } catch (err) {
      error.value = err.message || t('warehouse.errors.members')
    }
  }

  async function loadAssignments(fleetId = assignmentFleetId.value) {
    assignments.value = []
    if (!fleetId) return
    assignmentFleetId.value = fleetId
    try {
      assignments.value = await listWarehousePortAssignments(fleetId)
      await loadMembers(fleetId)
    } catch (err) {
      error.value = err.message || t('warehouse.errors.assignments')
    }
  }

  async function openAssignmentOverlay() {
    assignmentOverlayOpen.value = true
    if (!assignments.value.length && fleets.value.length) await loadAssignments(assignmentFleetId.value || fleets.value[0].id)
  }

  function closeAssignmentOverlay() {
    assignmentOverlayOpen.value = false
  }

  async function saveAssignment(assignment, event) {
    try {
      await updateWarehousePortAssignment(assignment.port_id, {
        fleet_id: Number(assignmentFleetId.value),
        assignee_user_id: event.target.value ? Number(event.target.value) : null,
      })
      await loadAssignments()
      success.value = t('warehouse.messages.assignmentUpdated')
    } catch (err) {
      error.value = err.message || t('warehouse.errors.assignments')
    }
  }

  async function publishOverview(fleetId = filters.fleet_id || fleets.value[0]?.id) {
    if (!fleetId) return
    publishingOverview.value = true
    error.value = ''
    try {
      await publishWarehouseOverviewWebhook(fleetId)
      success.value = t('warehouse.messages.overviewPublished')
    } catch (err) {
      error.value = err.message || t('warehouse.errors.overviewPublish')
    } finally {
      publishingOverview.value = false
    }
  }

  function resetDraft(values) {
    Object.assign(draft, createWarehouseDraft(), values)
  }

  async function openCreate() {
    editingId.value = null
    const fleetId = filters.fleet_id || fleets.value[0]?.id || ''
    resetDraft(createWarehouseDraft(fleetId))
    await loadMembers(fleetId)
    editorOpen.value = true
    error.value = ''
    success.value = ''
  }

  async function openEdit(entry) {
    editingId.value = entry.id
    resetDraft(warehouseDraftFromEntry(entry))
    await loadMembers(entry.fleet_id)
    editorOpen.value = true
    error.value = ''
    success.value = ''
  }

  function closeEditor() {
    editorOpen.value = false
    editingId.value = null
  }

  async function changeDraftFleet() {
    draft.member_user_id = ''
    await loadMembers(draft.fleet_id)
  }

  async function saveEntry() {
    const issue = warehouseDraftIssue(draft)
    if (issue) {
      error.value = t(`warehouse.validation.${issue}`)
      return
    }
    saving.value = true
    error.value = ''
    success.value = ''
    try {
      if (editingId.value) {
        await updateWarehouseEntry(editingId.value, warehousePayload(draft, { updating: true }))
        success.value = t('warehouse.messages.updated')
      } else {
        await createWarehouseEntry(warehousePayload(draft))
        success.value = t('warehouse.messages.created')
      }
      closeEditor()
      await loadEntries({ resetOffset: true })
    } catch (err) {
      if (err.status === 409) {
        closeEditor()
        await loadEntries({ resetOffset: true })
        error.value = t('warehouse.errors.conflict')
      } else {
        error.value = err.message || t('warehouse.errors.save')
      }
    } finally {
      saving.value = false
    }
  }

  async function removeEntry(entry) {
    if (!window.confirm(t('warehouse.actions.confirmDelete', { holder: entry.holder_name }))) return
    error.value = ''
    success.value = ''
    try {
      await deleteWarehouseEntry(entry.id, entry.version)
      success.value = t('warehouse.messages.deleted')
      await loadEntries({ resetOffset: true })
    } catch (err) {
      if (err.status === 409) {
        await loadEntries({ resetOffset: true })
        error.value = t('warehouse.errors.conflict')
      } else {
        error.value = err.message || t('warehouse.errors.delete')
      }
    }
  }

  async function clearFilters() {
    Object.assign(filters, { fleet_id: '', holder: '', port: '', resource: '', reserved: '', collection_status: '' })
    await loadEntries({ resetOffset: true })
  }

  onMounted(async () => {
    loading.value = true
    try {
      const [fleetRows, portRows, resourceRows] = await Promise.all([
        listWarehouseFleets(), listWarehousePorts(), listWarehouseResources(),
      ])
      fleets.value = fleetRows.filter((fleet) => fleet.is_active)
      ports.value = portRows
      resources.value = resourceRows
      if (canManageWarehouse.value) await loadAssignments(fleets.value[0]?.id || '')
      await loadEntries()
    } catch (err) {
      error.value = err.message || t('warehouse.errors.load')
      loading.value = false
    }
  })

  return {
    t, canManageWarehouse, page, fleets, members, ports, resources, assignments, assignmentFleetId, assignmentOverlayOpen, loading, saving, publishingOverview, error, success,
    editorOpen, editorTitle, editingId, draft, filters, formatAmount, formatDateTime, pageStart, pageEnd,
    hasPreviousPage, hasNextPage, loadEntries, previousPage, nextPage, openCreate,
    openEdit, closeEditor, changeDraftFleet, saveEntry, removeEntry, clearFilters,
    loadAssignments, openAssignmentOverlay, closeAssignmentOverlay, saveAssignment, publishOverview,
  }
}
