import { computed, onMounted, ref } from 'vue'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import { getPublicOfficialFleet } from '@/modules/fleet/api/fleet'

export function useLandingPage() {
  const { t } = useLocale()
  const { isAuthenticated } = useSession()
  const publicFleet = ref(null)

  onMounted(async () => {
    try {
      publicFleet.value = await getPublicOfficialFleet()
    } catch {
      publicFleet.value = null
    }
  })

  const newcomerSteps = computed(() => [
    { number: '01', icon: 'compass', title: t('home.newcomer.guideTitle'), text: t('home.newcomer.guideText'), path: '/new-captain' },
    { number: '02', icon: 'guides', title: t('home.newcomer.learnTitle'), text: t('home.newcomer.learnText'), path: '/guides' },
    { number: '03', icon: 'builds', title: t('home.newcomer.prepareTitle'), text: t('home.newcomer.prepareText'), path: '/builds' },
    { number: '04', icon: 'forum', title: t('home.newcomer.askTitle'), text: t('home.newcomer.askText'), path: '/forum' },
    { number: '05', icon: 'calendar', title: t('home.newcomer.joinTitle'), text: t('home.newcomer.joinText'), path: '/calendar' },
  ])

  const memberModules = computed(() => [
    { icon: 'compass', title: t('common.newCaptainGuide'), text: t('home.newcomer.guideText'), path: '/new-captain' },
    { icon: 'builds', title: t('home.showcase.builds.title'), text: t('home.showcase.builds.description'), path: '/builds' },
    { icon: 'guides', title: t('home.showcase.guides.title'), text: t('home.showcase.guides.description'), path: '/guides' },
    { icon: 'forum', title: t('home.showcase.forum.title'), text: t('home.showcase.forum.description'), path: '/forum' },
    { icon: 'calendar', title: t('home.showcase.calendar.title'), text: t('home.showcase.calendar.description'), path: '/calendar' },
  ])

  function memberRoute(path) {
    if (isAuthenticated.value) return path
    return { name: 'login', query: { redirect: path } }
  }

  return {
    t,
    isAuthenticated,
    publicFleet,
    newcomerSteps,
    memberModules,
    memberRoute,
  }
}
