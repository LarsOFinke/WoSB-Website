import { computed, reactive, ref } from 'vue'

import {
  assignAdminBuildRole,
  createBuildRole,
  deleteAdminBuild,
  deleteBuildRole,
  listAdminBuilds,
  listBuildRoles,
  updateBuildRole,
} from '@/modules/admin/api/admin'
import { filterAdminBuilds } from '@/modules/admin/domain/adminWorkspace'
import { useDebouncedWatch } from '@/shared/composables/useDebouncedWatch'

export function useAdminBuilds({ isStaff, t, clearConfirmation }) {
  const builds = ref([])
  const buildRoles = ref([])
  const roleDrafts = reactive({})
  const newBuildRole = reactive({ slug: '', label: '', description: '', sort_order: 50 })
  const search = ref('')
  const buildType = ref('')
  const buildRate = ref('')
  const buildVisibility = ref('')
  const loading = ref(false)
  const error = ref('')
  const roleBusy = ref('')
  const roleMessage = ref('')
  const pendingRoleDelete = ref('')

  const filteredBuilds = computed(() => filterAdminBuilds(builds.value, {
    rate: buildRate.value,
    visibility: buildVisibility.value,
  }))
  const buildRates = computed(() => [...new Set(builds.value
    .map((build) => build.ship?.rate)
    .filter((rate) => rate !== null && rate !== undefined))]
    .sort((left, right) => Number(left) - Number(right)))
  const buildCountLabel = computed(() => filteredBuilds.value.length === 1
    ? t('admin.builds.summaryOne')
    : t('admin.builds.summaryMany', { count: filteredBuilds.value.length }))

  function hydrateRoleDrafts(roles) {
    for (const key of Object.keys(roleDrafts)) delete roleDrafts[key]
    for (const role of roles) {
      roleDrafts[role.slug] = {
        label: role.label,
        description: role.description || '',
        sort_order: Number(role.sort_order || 0),
      }
    }
  }

  async function loadBuilds() {
    if (!isStaff.value) return
    loading.value = true
    error.value = ''
    try {
      const [nextBuilds, nextRoles] = await Promise.all([
        listAdminBuilds(search.value, buildType.value),
        listBuildRoles(),
      ])
      builds.value = nextBuilds
      buildRoles.value = nextRoles
      hydrateRoleDrafts(nextRoles)
    } catch (err) {
      error.value = err.message || t('admin.builds.loadError')
    } finally {
      loading.value = false
    }
  }

  async function confirmDeleteBuild(buildId) {
    error.value = ''
    try {
      await deleteAdminBuild(buildId)
      clearConfirmation()
      await loadBuilds()
    } catch (err) {
      error.value = err.message || t('admin.builds.deleteError')
    }
  }

  async function submitBuildRole() {
    roleBusy.value = 'create'
    error.value = ''
    roleMessage.value = ''
    try {
      await createBuildRole({
        slug: newBuildRole.slug.trim().toLowerCase(),
        label: newBuildRole.label.trim(),
        description: newBuildRole.description.trim() || null,
        sort_order: Number(newBuildRole.sort_order || 0),
      })
      Object.assign(newBuildRole, { slug: '', label: '', description: '', sort_order: 50 })
      roleMessage.value = t('admin.buildRoles.created')
      await loadBuilds()
    } catch (err) {
      error.value = err.message || t('admin.buildRoles.createError')
    } finally {
      roleBusy.value = ''
    }
  }

  async function saveBuildRole(slug) {
    const draft = roleDrafts[slug]
    if (!draft) return
    roleBusy.value = `save:${slug}`
    error.value = ''
    roleMessage.value = ''
    try {
      await updateBuildRole(slug, {
        label: draft.label.trim(),
        description: draft.description.trim() || null,
        sort_order: Number(draft.sort_order || 0),
      })
      roleMessage.value = t('admin.buildRoles.saved')
      await loadBuilds()
    } catch (err) {
      error.value = err.message || t('admin.buildRoles.saveError')
    } finally {
      roleBusy.value = ''
    }
  }

  function askDeleteBuildRole(slug) {
    pendingRoleDelete.value = slug
    roleMessage.value = ''
  }

  function cancelDeleteBuildRole() {
    pendingRoleDelete.value = ''
  }

  async function removeBuildRole(slug) {
    roleBusy.value = `delete:${slug}`
    error.value = ''
    roleMessage.value = ''
    try {
      await deleteBuildRole(slug)
      pendingRoleDelete.value = ''
      roleMessage.value = t('admin.buildRoles.deleted')
      if (buildType.value === slug) buildType.value = ''
      await loadBuilds()
    } catch (err) {
      error.value = err.message || t('admin.buildRoles.deleteError')
    } finally {
      roleBusy.value = ''
    }
  }

  async function changeBuildRole(build, event) {
    const nextRole = event.target.value
    const previousRole = build.build_type
    if (!nextRole || nextRole === previousRole) return
    build.build_type = nextRole
    build.build_role_label = buildRoles.value.find((role) => role.slug === nextRole)?.label || nextRole
    roleBusy.value = `assign:${build.id}`
    error.value = ''
    try {
      const updated = await assignAdminBuildRole(build.id, nextRole)
      Object.assign(build, updated)
    } catch (err) {
      build.build_type = previousRole
      build.build_role_label = buildRoles.value.find((role) => role.slug === previousRole)?.label || previousRole
      error.value = err.message || t('admin.buildRoles.assignError')
    } finally {
      roleBusy.value = ''
    }
  }

  function resetBuildFilters() {
    search.value = ''
    buildType.value = ''
    buildRate.value = ''
    buildVisibility.value = ''
  }

  useDebouncedWatch([search, buildType], loadBuilds, 220)

  return {
    builds, buildRoles, roleDrafts, newBuildRole, search, buildType, buildRate,
    buildVisibility, loading, error, roleBusy, roleMessage, pendingRoleDelete,
    filteredBuilds, buildRates, buildCountLabel,
    loadBuilds, confirmDeleteBuild, submitBuildRole, saveBuildRole, askDeleteBuildRole,
    cancelDeleteBuildRole, removeBuildRole,
    changeBuildRole, resetBuildFilters,
  }
}
