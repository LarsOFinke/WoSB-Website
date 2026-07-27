import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useLocale } from '@/locales'
import { localDateTimeValue, localDateFromInputs } from '@/shared/datetime/localDateTime'
import { createGroup } from '@/modules/groups/api/groups'

export function useGroupCreatePage() {
  const router = useRouter()
  const { t } = useLocale()
  const saving = ref(false)
  const error = ref('')

  const focusOptions = [
    'pve_farming',
    'pve_imp_hunting',
    'pve_general',
    'pvp_open_world',
    'pvp_arena',
    'pvp_general',
    'trading',
    'other',
  ]

  const rateOptions = [7, 6, 5, 4, 3, 2, 1]

  const form = reactive({
    title: '',
    focus: 'pve_general',
    description: '',
    expectations: '',
    activity_plan: '',
    contact_note: '',
    scheduled_start_date: '',
    scheduled_start_time: '',
    scheduled_end_date: '',
    scheduled_end_time: '',
    max_members: 5,
    allow_guests: false,
    min_ship_rate: '',
    max_ship_rate: '',
    fleet_restriction: '',
  })

  const rateRangeInvalid = computed(() =>
    form.min_ship_rate && form.max_ship_rate && Number(form.max_ship_rate) > Number(form.min_ship_rate),
  )

  const scheduledStartAt = computed(() => localDateTimeValue(form.scheduled_start_date, form.scheduled_start_time))
  const scheduledEndAt = computed(() => localDateTimeValue(form.scheduled_end_date, form.scheduled_end_time))
  const scheduleHasAnyValue = computed(() => Boolean(
    form.scheduled_start_date
    || form.scheduled_start_time
    || form.scheduled_end_date
    || form.scheduled_end_time,
  ))
  const scheduleIncomplete = computed(() => scheduleHasAnyValue.value && !(
    scheduledStartAt.value && scheduledEndAt.value
  ))
  const timeRangeInvalid = computed(() => {
    if (!scheduledStartAt.value || !scheduledEndAt.value) return false
    const start = localDateFromInputs(form.scheduled_start_date, form.scheduled_start_time)
    const end = localDateFromInputs(form.scheduled_end_date, form.scheduled_end_time)
    return !start || !end || end <= start
  })

  async function submitGroup() {
    error.value = ''
    if (rateRangeInvalid.value) {
      error.value = t('groups.create.rateRangeInvalid')
      return
    }
    if (scheduleIncomplete.value) {
      error.value = t('groups.create.scheduleIncomplete')
      return
    }
    if (timeRangeInvalid.value) {
      error.value = t('groups.create.timeRangeInvalid')
      return
    }

    saving.value = true
    try {
      const created = await createGroup({
        title: form.title,
        focus: form.focus,
        description: form.description || null,
        expectations: form.expectations || null,
        activity_plan: form.activity_plan || null,
        contact_note: form.contact_note || null,
        scheduled_start_at: scheduledStartAt.value || null,
        scheduled_end_at: scheduledEndAt.value || null,
        max_members: Number(form.max_members) || 5,
        min_ship_rate: form.min_ship_rate ? Number(form.min_ship_rate) : null,
        max_ship_rate: form.max_ship_rate ? Number(form.max_ship_rate) : null,
        allow_guests: Boolean(form.allow_guests),
        fleet_restriction: form.fleet_restriction || null,
      })
      router.push(`/groups/${created.id}`)
    } catch (err) {
      error.value = err.message || t('groups.create.saveError')
    } finally {
      saving.value = false
    }
  }

  return {
    router,
    t,
    saving,
    error,
    focusOptions,
    rateOptions,
    form,
    rateRangeInvalid,
    scheduledStartAt,
    scheduledEndAt,
    scheduleHasAnyValue,
    scheduleIncomplete,
    timeRangeInvalid,
    submitGroup,
    localDateTimeValue,
    localDateFromInputs,
  }
}
