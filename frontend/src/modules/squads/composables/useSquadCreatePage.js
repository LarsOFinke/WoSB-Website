import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useLocale } from '@/locales'
import { createSquad, listSquadRoster } from '@/modules/squads/api/squads'

export function useSquadCreatePage() {
  const router = useRouter()
  const { t } = useLocale()

  const roster = ref([])
  const loading = ref(false)
  const saving = ref(false)
  const error = ref('')
  const form = reactive({
    name: '',
    description: '',
    focus: '',
    maxMembers: 12,
    leaderMembershipId: '',
  })

  const rosterOptions = computed(() => [...roster.value].sort((left, right) => left.display_name.localeCompare(right.display_name)))

  async function loadRoster() {
    loading.value = true
    error.value = ''
    try {
      roster.value = await listSquadRoster()
    } catch (err) {
      error.value = err.message || t('squads.create.rosterError')
    } finally {
      loading.value = false
    }
  }

  async function submitSquad() {
    saving.value = true
    error.value = ''
    try {
      const squad = await createSquad({
        name: form.name,
        description: form.description || null,
        focus: form.focus || null,
        max_members: form.maxMembers ? Number(form.maxMembers) : null,
        leader_membership_id: Number(form.leaderMembershipId),
      })
      router.push(`/squads/${squad.id}`)
    } catch (err) {
      error.value = err.message || t('squads.create.saveError')
    } finally {
      saving.value = false
    }
  }

  onMounted(loadRoster)

  return {
    router,
    t,
    roster,
    loading,
    saving,
    error,
    form,
    rosterOptions,
    loadRoster,
    submitSquad,
  }
}
