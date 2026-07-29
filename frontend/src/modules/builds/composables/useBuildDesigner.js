import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import { createBuild, deleteMyBuild, getBuild, getBuildOptions, updateMyBuild } from '@/modules/builds/api/builds'
import { createBuildForm, slotLimits, sortShipsForDropdown, weaponArcFields } from '@/modules/builds/buildForm'
import { useBuildCatalog } from '@/modules/builds/composables/useBuildCatalog'
import { useBuildCrew } from '@/modules/builds/composables/useBuildCrew'
import { useBuildEffects } from '@/modules/builds/composables/useBuildEffects'
import { useBuildInventory } from '@/modules/builds/composables/useBuildInventory'
import { createBuildPayload, hydrateBuildForm, resetBuildSlots } from '@/modules/builds/domain/buildDesignerForm'
import { listShips } from '@/modules/ships/api/ships'

const EMPTY_CATALOG = {
  build_roles: [],
  categories: [],
  options: {},
  stat_definitions: [],
  research_upgrade_slot_effects: {},
  limits: {},
}

export function useBuildDesigner(props, { slotPlaceholderSrc }) {
  const router = useRouter()
  const { optionLabel, t } = useLocale()
  const { user } = useSession()
  const form = reactive(createBuildForm())
  const ships = ref([])
  const optionCatalog = ref({ ...EMPTY_CATALOG })
  const loading = ref(false)
  const saving = ref(false)
  const deleting = ref(false)
  const error = ref('')
  const suppressShipChange = ref(false)
  const isEditing = computed(() => Boolean(props.id))
  const selectedShip = computed(() => ships.value.find((ship) => ship.id === Number(form.ship_id)))

  const catalog = useBuildCatalog({
    optionCatalog,
    selectedShip,
    optionLabel,
    t,
    slotPlaceholderSrc,
  })
  const inventory = useBuildInventory({
    form,
    optionCatalog,
    selectedShip,
    optionMeta: catalog.optionMeta,
    optionLabel,
  })
  const effects = useBuildEffects({
    form,
    optionCatalog,
    selectedShip,
    optionLabel,
    t,
    catalog,
    inventory,
    saving,
  })
  const crew = useBuildCrew({
    form,
    crewCapacity: effects.crewCapacity,
    sailorMinimum: effects.sailorMinimum,
  })

  const buildPayload = () => createBuildPayload(form)
  const resetSlots = () => resetBuildSlots(form, inventory.slotLimitForField)
  const hydrateBuild = (build) => hydrateBuildForm(form, build, inventory.slotLimitForField)

  function reconcileBuildRole() {
    const roles = optionCatalog.value.build_roles || []
    if (roles.length && !roles.some((role) => role.slug === form.build_type)) {
      form.build_type = roles[0].slug
    }
  }

  async function saveBuild() {
    error.value = ''
    if (!effects.canSubmit.value) return
    saving.value = true
    try {
      const saved = isEditing.value
        ? await updateMyBuild(props.id, buildPayload())
        : await createBuild(buildPayload())
      await router.push(`/builds/${saved.id}`)
    } catch (err) {
      error.value = err.message || t(isEditing.value ? 'builds.edit.saveError' : 'builds.create.saveError')
    } finally {
      saving.value = false
    }
  }

  async function deleteBuild() {
    if (!isEditing.value || saving.value || deleting.value) return
    if (!window.confirm(t('myBuilds.confirmDelete'))) return
    deleting.value = true
    error.value = ''
    try {
      await deleteMyBuild(props.id)
      await router.replace('/profile/builds')
    } catch (err) {
      error.value = err.message || t('myBuilds.deleteError')
    } finally {
      deleting.value = false
    }
  }

  let optionRequestId = 0
  watch(() => form.ship_id, async (shipId) => {
    if (suppressShipChange.value) return
    form.mortar_modification_installed = false
    crew.resetCrewAllocation()
    if (!shipId) return
    const requestId = ++optionRequestId
    try {
      const options = await getBuildOptions(Number(shipId))
      if (requestId !== optionRequestId) return
      optionCatalog.value = options
      reconcileBuildRole()
      for (const arc of weaponArcFields) inventory.reconcileInventoryField(arc.fieldName)
    } catch (err) {
      if (requestId === optionRequestId) error.value = err.message || t('builds.create.loadError')
    }
  })

  watch(() => form.mortar_modification_installed, () => {
    for (const fieldName of [
      'port_weapon_slots',
      'starboard_weapon_slots',
      'mortar_weapon_slots',
    ]) {
      inventory.reconcileInventoryField(fieldName)
    }
  })

  for (const [access, fieldName] of [
    [effects.upgradeSlot5Unlocked, 'upgrade_5'],
    [effects.upgradeSlot6Available, 'upgrade_6'],
    [effects.upgradeSlot7Available, 'upgrade_7'],
    [effects.upgradeSlot8Available, 'upgrade_8'],
  ]) {
    watch(access, (isAvailable) => {
      if (!isAvailable) form[fieldName] = ''
    })
  }

  onMounted(async () => {
    loading.value = true
    error.value = ''
    try {
      ships.value = sortShipsForDropdown(await listShips())
      if (isEditing.value) {
        const existing = await getBuild(props.id)
        if (Number(existing.owner_id) !== Number(user.value?.id) || existing.is_official_template) {
          throw new Error(t('builds.edit.notAllowed'))
        }
        suppressShipChange.value = true
        form.ship_id = existing.ship_id
        optionCatalog.value = await getBuildOptions(existing.ship_id)
        hydrateBuild(existing)
        reconcileBuildRole()
        for (const fieldName of Object.keys(slotLimits)) inventory.reconcileInventoryField(fieldName)
        suppressShipChange.value = false
      } else {
        form.ship_id = ships.value[0]?.id || ''
        optionCatalog.value = await getBuildOptions(form.ship_id || null)
        reconcileBuildRole()
        resetSlots()
        crew.resetCrewAllocation()
      }
    } catch (err) {
      suppressShipChange.value = false
      error.value = err.message || t(isEditing.value ? 'builds.edit.loadError' : 'builds.create.loadError')
    } finally {
      loading.value = false
    }
  })

  return {
    optionLabel,
    t,
    isEditing,
    ships,
    optionCatalog,
    loading,
    saving,
    deleting,
    error,
    form,
    selectedShip,
    saveBuild,
    deleteBuild,
    ...catalog,
    ...inventory,
    ...effects,
    ...crew,
  }
}
