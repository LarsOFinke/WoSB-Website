<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'

import { useLocale } from '@/locales'
import { createModerator, deleteAdminBuild, listAdminBuilds, listUsers } from '@/services/admin'
import { useSession } from '@/services/session'

const { t } = useLocale()
const { isAdmin, isStaff, loadSession, sessionState, user } = useSession()

const activeTab = ref('status')
const builds = ref([])
const users = ref([])
const search = ref('')
const loading = ref(false)
const userLoading = ref(false)
const error = ref('')
const userError = ref('')
const moderatorSuccess = ref('')
const pendingDeleteId = ref(null)
const apiStatus = ref(t('admin.status.loading'))
const apiStatusDetail = ref(t('admin.status.loadingDetail'))
let searchTimer = null

const moderatorForm = reactive({
  username: '',
  display_name: '',
  password: '',
})

const buildCountLabel = computed(() =>
  builds.value.length === 1
    ? t('admin.builds.summaryOne')
    : t('admin.builds.summaryMany', { count: builds.value.length }),
)

const userCountLabel = computed(() =>
  users.value.length === 1 ? t('admin.users.summaryOne') : t('admin.users.summaryMany', { count: users.value.length }),
)

function crewTotal(build) {
  return build.sailors + build.soldiers + build.musketeers + build.mercenaries
}

async function loadBuilds() {
  if (!isStaff.value) return
  loading.value = true
  error.value = ''
  try {
    builds.value = await listAdminBuilds(search.value)
  } catch (err) {
    error.value = err.message || t('admin.builds.loadError')
  } finally {
    loading.value = false
  }
}

async function loadUsers() {
  if (!isAdmin.value) return
  userLoading.value = true
  userError.value = ''
  try {
    users.value = await listUsers()
  } catch (err) {
    userError.value = err.message || t('admin.users.loadError')
  } finally {
    userLoading.value = false
  }
}

async function loadStatus() {
  if (!isStaff.value) return
  apiStatus.value = t('admin.status.loading')
  apiStatusDetail.value = t('admin.status.loadingDetail')
  try {
    const response = await fetch('/api/health')
    if (!response.ok) throw new Error(`API responded with ${response.status}`)
    const payload = await response.json()
    apiStatus.value = t('admin.status.online')
    apiStatusDetail.value = payload.status
      ? t('admin.status.detailWithStatus', { status: payload.status })
      : t('admin.status.onlineDetail')
  } catch {
    apiStatus.value = t('admin.status.offline')
    apiStatusDetail.value = t('admin.status.offlineDetail')
  }
}

async function confirmDelete(buildId) {
  error.value = ''
  try {
    await deleteAdminBuild(buildId)
    pendingDeleteId.value = null
    await loadBuilds()
  } catch (err) {
    error.value = err.message || t('admin.builds.deleteError')
  }
}

async function submitModerator() {
  userError.value = ''
  moderatorSuccess.value = ''
  try {
    await createModerator({ ...moderatorForm })
    moderatorForm.username = ''
    moderatorForm.display_name = ''
    moderatorForm.password = ''
    moderatorSuccess.value = t('admin.users.moderatorCreated')
    await loadUsers()
  } catch (err) {
    userError.value = err.message || t('admin.users.createModeratorError')
  }
}

watch(search, () => {
  window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(loadBuilds, 220)
})

watch(activeTab, async (tab) => {
  if (tab === 'builds') await loadBuilds()
  if (tab === 'status') await loadStatus()
  if (tab === 'users') await loadUsers()
})

onMounted(async () => {
  if (!sessionState.isReady) {
    await loadSession()
  }
  await loadStatus()
})
</script>

<template>
  <section class="admin-page" aria-labelledby="admin-title">
    <div class="wire-frame page-frame admin-frame">
      <header class="wire-section admin-hero refined-admin-hero">
        <div>
          <p class="eyebrow">{{ t('admin.eyebrow') }}</p>
          <h1 id="admin-title">{{ isAdmin ? t('admin.title') : t('admin.moderatorTitle') }}</h1>
          <p>{{ isAdmin ? t('admin.subtitle') : t('admin.moderatorSubtitle') }}</p>
        </div>
        <span v-if="user" class="summary-pill">{{ t(`roles.${user.role}`) }}</span>
      </header>

      <section v-if="!isStaff" class="wire-section admin-locked">
        <h2>{{ t('admin.lockedTitle') }}</h2>
        <p>{{ t('admin.lockedText') }}</p>
        <RouterLink class="button-box primary-action" to="/login">{{ t('auth.login') }}</RouterLink>
      </section>

      <template v-else>
        <section class="wire-section admin-tabs" :aria-label="t('admin.tabsLabel')">
          <button class="tab-button" :class="{ 'is-active': activeTab === 'status' }" type="button" @click="activeTab = 'status'">
            {{ t('admin.tabs.status') }}
          </button>
          <button class="tab-button" :class="{ 'is-active': activeTab === 'builds' }" type="button" @click="activeTab = 'builds'">
            {{ t('admin.tabs.builds') }}
          </button>
          <button v-if="isAdmin" class="tab-button" :class="{ 'is-active': activeTab === 'users' }" type="button" @click="activeTab = 'users'">
            {{ t('admin.tabs.users') }}
          </button>
        </section>

        <section v-if="activeTab === 'status'" class="wire-section admin-panel admin-status-panel">
          <div class="admin-panel-heading">
            <div>
              <h2>{{ t('admin.status.title') }}</h2>
              <p>{{ t('admin.status.subtitle') }}</p>
            </div>
          </div>

          <aside class="home-status-card refined-status-card admin-status-card" aria-live="polite">
            <span>{{ t('admin.status.cardLabel') }}</span>
            <strong>{{ apiStatus }}</strong>
            <p>{{ apiStatusDetail }}</p>
          </aside>
        </section>

        <section v-if="activeTab === 'builds'" class="wire-section admin-panel">
          <div class="admin-panel-heading">
            <div>
              <h2>{{ t('admin.builds.title') }}</h2>
              <p>{{ t('admin.builds.subtitle') }}</p>
            </div>
            <span class="summary-pill">{{ buildCountLabel }}</span>
          </div>

          <label class="filter-box admin-search">
            <input v-model="search" type="search" :placeholder="t('admin.builds.searchPlaceholder')" />
          </label>

          <p v-if="loading" class="muted table-state">{{ t('admin.builds.loading') }}</p>
          <p v-else-if="error" class="error-text table-state">{{ error }}</p>
          <p v-else-if="builds.length === 0" class="muted table-state">{{ t('admin.builds.empty') }}</p>

          <div v-else class="admin-build-list">
            <article v-for="build in builds" :key="build.id" class="admin-build-row">
              <div class="admin-build-main">
                <strong>{{ build.build_name }}</strong>
                <span>
                  {{ build.ship.name }} · {{ t('common.rate') }} {{ build.ship.rate }} ·
                  {{ t(`builds.types.${build.build_type}`) }} ·
                  {{ t('builds.list.crew', { current: crewTotal(build), max: build.ship.crew_capacity }) }}
                </span>
              </div>

              <div v-if="pendingDeleteId === build.id" class="delete-confirmation">
                <span>{{ t('admin.builds.confirmDelete') }}</span>
                <button class="danger-action" type="button" @click="confirmDelete(build.id)">
                  {{ t('admin.builds.deleteNow') }}
                </button>
                <button class="small-action" type="button" @click="pendingDeleteId = null">
                  {{ t('common.cancel') }}
                </button>
              </div>

              <button v-else class="danger-action" type="button" @click="pendingDeleteId = build.id">
                {{ t('admin.builds.delete') }}
              </button>
            </article>
          </div>
        </section>

        <section v-if="activeTab === 'users' && isAdmin" class="wire-section admin-panel admin-users-panel">
          <div class="admin-panel-heading">
            <div>
              <h2>{{ t('admin.users.title') }}</h2>
              <p>{{ t('admin.users.subtitle') }}</p>
            </div>
            <span class="summary-pill">{{ userCountLabel }}</span>
          </div>

          <form class="moderator-form" @submit.prevent="submitModerator">
            <label class="input-panel embedded-field">
              <span>{{ t('auth.username') }}</span>
              <input v-model="moderatorForm.username" required minlength="3" maxlength="80" />
            </label>
            <label class="input-panel embedded-field">
              <span>{{ t('profile.displayName') }}</span>
              <input v-model="moderatorForm.display_name" required maxlength="120" />
            </label>
            <label class="input-panel embedded-field">
              <span>{{ t('auth.password') }}</span>
              <input v-model="moderatorForm.password" type="password" required minlength="6" />
            </label>
            <button class="form-button primary-action" type="submit">{{ t('admin.users.createModerator') }}</button>
          </form>

          <p v-if="userLoading" class="muted table-state">{{ t('admin.users.loading') }}</p>
          <p v-if="userError" class="error-text table-state">{{ userError }}</p>
          <p v-if="moderatorSuccess" class="success-text table-state">{{ moderatorSuccess }}</p>

          <div class="admin-user-list">
            <article v-for="row in users" :key="row.id" class="admin-user-row">
              <div>
                <strong>{{ row.display_name }}</strong>
                <span>{{ row.username }}</span>
              </div>
              <span class="summary-pill">{{ t(`roles.${row.role}`) }}</span>
            </article>
          </div>
        </section>
      </template>
    </div>
  </section>
</template>
