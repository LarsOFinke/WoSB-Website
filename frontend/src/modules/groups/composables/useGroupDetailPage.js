import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useLocale } from '@/locales'
import { listMyBuilds } from '@/modules/builds/api/builds'
import { closeGroup, getGroup, joinGroup } from '@/modules/groups/api/groups'
import {
  createGroupJoinForm,
  formatGroupDateTime,
  groupJoinPayload,
  groupMemberShipLabel,
  groupRateRequirement,
  groupSchedule,
  isGroupShipAllowed,
} from '@/modules/groups/domain/groupDetail'
import { listShips } from '@/modules/ships/api/ships'
import { useSession } from '@/modules/accounts/session'

export function useGroupDetailPage(props) {
  const { locale, t } = useLocale()
  const { isAuthenticated, isStaff, user } = useSession()
  const group = ref(null)
  const ships = ref([])
  const builds = ref([])
  const loading = ref(false)
  const joining = ref(false)
  const closing = ref(false)
  const error = ref('')
  const joinError = ref('')
  const joinSuccess = ref('')
  const joinForm = reactive(createGroupJoinForm())

  const canManage = computed(() => Boolean(group.value && isStaff.value))
  const canJoin = computed(() => Boolean(group.value?.is_joinable))
  const selectedBuild = computed(() => builds.value.find((build) => String(build.id) === String(joinForm.build_id)) || null)
  const selectedShip = computed(() => selectedBuild.value?.ship
    || ships.value.find((ship) => String(ship.id) === String(joinForm.ship_id))
    || null)
  const allowedShips = computed(() => ships.value.filter((ship) => isShipAllowed(ship.rate)))
  const allowedBuilds = computed(() => builds.value.filter((build) => isShipAllowed(build.ship?.rate)))
  const rateRequirementText = computed(() => groupRateRequirement(group.value, t))
  const scheduleText = computed(() => groupSchedule(group.value, t, locale.value))

  function formatDateTime(value) {
    return formatGroupDateTime(value, locale.value)
  }

  function isShipAllowed(rate) {
    return isGroupShipAllowed(group.value, rate)
  }

  function memberShipLabel(member) {
    return groupMemberShipLabel(member, t)
  }

  async function loadAuxiliaryData() {
    try {
      ships.value = await listShips()
    } catch {
      ships.value = []
    }
    if (!isAuthenticated.value) {
      builds.value = []
      return
    }
    try {
      const page = await listMyBuilds('', '', '', 100, 0)
      builds.value = page.items || []
    } catch {
      builds.value = []
    }
  }

  async function loadGroup() {
    loading.value = true
    error.value = ''
    try {
      group.value = await getGroup(props.id)
      if (!joinForm.display_name && user.value) joinForm.display_name = user.value.display_name || user.value.username || ''
    } catch (err) {
      error.value = err.message || t('groups.detail.loadError')
    } finally {
      loading.value = false
    }
  }

  async function submitJoin() {
    joining.value = true
    joinError.value = ''
    joinSuccess.value = ''
    try {
      await joinGroup(group.value.id, groupJoinPayload(joinForm, user.value, selectedShip.value))
      joinSuccess.value = t('groups.detail.joined')
      joinForm.note = ''
      await loadGroup()
    } catch (err) {
      joinError.value = err.message || t('groups.detail.joinError')
    } finally {
      joining.value = false
    }
  }

  async function submitClose() {
    closing.value = true
    error.value = ''
    try {
      await closeGroup(group.value.id)
      await loadGroup()
    } catch (err) {
      error.value = err.message || t('groups.detail.closeError')
    } finally {
      closing.value = false
    }
  }

  watch(() => joinForm.build_id, (value) => {
    if (value) joinForm.ship_id = ''
  })
  watch(() => joinForm.ship_id, (value) => {
    if (value) joinForm.build_id = ''
  })
  onMounted(async () => {
    await Promise.all([loadGroup(), loadAuxiliaryData()])
  })

  return {
    locale, t, isAuthenticated, group, ships, builds, loading,
    joining, closing, error, joinError, joinSuccess, joinForm, canManage, canJoin,
    selectedBuild, selectedShip, allowedShips, allowedBuilds, rateRequirementText,
    scheduleText, formatDateTime, isShipAllowed, memberShipLabel, loadAuxiliaryData,
    loadGroup, submitJoin, submitClose,
  }
}
