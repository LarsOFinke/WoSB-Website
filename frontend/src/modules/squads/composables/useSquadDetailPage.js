import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import {
  SQUAD_ROLES,
  addSquadMember,
  archiveSquad,
  getSquad,
  listSquadRoster,
  removeSquadMember,
  updateSquad,
  updateSquadMember,
} from '@/modules/squads/api/squads'
import {
  availableSquadRoster,
  canRemoveSquadMember,
  createSquadEditForm,
  createSquadMemberForm,
  squadMemberCreatePayload,
  squadMemberUpdatePayload,
  squadUpdatePayload,
  syncSquadForms,
} from '@/modules/squads/domain/squadManagement'

export function useSquadDetailPage(props) {
  const router = useRouter()
  const { t } = useLocale()
  const { canManageFleet } = useSession()
  const squad = ref(null)
  const roster = ref([])
  const loading = ref(false)
  const saving = ref(false)
  const memberSavingId = ref(null)
  const adding = ref(false)
  const archiving = ref(false)
  const error = ref('')
  const success = ref('')
  const editForm = reactive(createSquadEditForm())
  const addForm = reactive(createSquadMemberForm())
  const memberDrafts = reactive({})

  const availableRoster = computed(() => availableSquadRoster(roster.value, squad.value?.members))
  const roleOptions = computed(() => SQUAD_ROLES.map((value) => ({ value, label: t(`squads.roles.${value}`) })))
  const addRoleOptions = computed(() => squad.value?.can_administer
    ? roleOptions.value
    : roleOptions.value.filter((option) => option.value === 'member'))
  const canArchive = computed(() => canManageFleet.value && squad.value?.is_active)

  function syncDrafts() {
    syncSquadForms(squad.value, editForm, memberDrafts)
  }

  async function loadSquad() {
    loading.value = true
    error.value = ''
    try {
      squad.value = await getSquad(props.id)
      syncDrafts()
      if (squad.value.can_manage) {
        try {
          roster.value = await listSquadRoster()
        } catch {
          roster.value = []
        }
      }
    } catch (err) {
      error.value = err.message || t('squads.detail.loadError')
    } finally {
      loading.value = false
    }
  }

  async function saveSquad() {
    saving.value = true
    error.value = ''
    success.value = ''
    try {
      squad.value = await updateSquad(props.id, squadUpdatePayload(editForm))
      syncDrafts()
      success.value = t('squads.detail.saved')
    } catch (err) {
      error.value = err.message || t('squads.detail.saveError')
    } finally {
      saving.value = false
    }
  }

  async function addMember() {
    adding.value = true
    error.value = ''
    success.value = ''
    try {
      squad.value = await addSquadMember(props.id, squadMemberCreatePayload(addForm))
      Object.assign(addForm, createSquadMemberForm())
      syncDrafts()
      success.value = t('squads.detail.memberAdded')
    } catch (err) {
      error.value = err.message || t('squads.detail.memberError')
    } finally {
      adding.value = false
    }
  }

  async function saveMember(member) {
    const draft = memberDrafts[member.id]
    if (!draft) return
    memberSavingId.value = member.id
    error.value = ''
    success.value = ''
    try {
      squad.value = await updateSquadMember(props.id, member.id, squadMemberUpdatePayload(draft))
      syncDrafts()
      success.value = t('squads.detail.memberSaved')
    } catch (err) {
      error.value = err.message || t('squads.detail.memberError')
    } finally {
      memberSavingId.value = null
    }
  }

  function canRemove(member) {
    return canRemoveSquadMember(squad.value, member)
  }

  async function removeMember(member) {
    if (!window.confirm(t('squads.detail.removeConfirm', { name: member.display_name }))) return
    memberSavingId.value = member.id
    error.value = ''
    success.value = ''
    try {
      squad.value = await removeSquadMember(props.id, member.id)
      delete memberDrafts[member.id]
      syncDrafts()
      success.value = t('squads.detail.memberRemoved')
    } catch (err) {
      error.value = err.message || t('squads.detail.memberError')
    } finally {
      memberSavingId.value = null
    }
  }

  async function archiveCurrentSquad() {
    if (!window.confirm(t('squads.detail.archiveConfirm'))) return
    archiving.value = true
    error.value = ''
    try {
      await archiveSquad(props.id)
      router.push('/squads')
    } catch (err) {
      error.value = err.message || t('squads.detail.archiveError')
    } finally {
      archiving.value = false
    }
  }

  onMounted(loadSquad)

  return {
    router, t, canManageFleet, squad, roster, loading, saving, memberSavingId,
    adding, archiving, error, success, editForm, addForm, memberDrafts,
    availableRoster, roleOptions, addRoleOptions, canArchive, syncDrafts,
    loadSquad, saveSquad, addMember, saveMember, canRemove, removeMember,
    archiveCurrentSquad,
  }
}
