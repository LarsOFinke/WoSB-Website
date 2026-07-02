<template>
  <section class="grid grid-2">
    <form class="card" @submit.prevent="saveProfile">
      <h1>Profil</h1>
      <MessageBox :message="message" />

      <div class="form-row">
        <label for="displayName">Anzeigename</label>
        <input id="displayName" v-model.trim="profile.display_name" class="input" />
      </div>

      <div class="form-row">
        <label for="mainRole">Hauptrolle</label>
        <input id="mainRole" v-model.trim="profile.main_role" class="input" />
      </div>

      <div class="form-row">
        <label for="fleet">Flotte</label>
        <input id="fleet" v-model.trim="profile.fleet" class="input" />
      </div>

      <div class="form-row">
        <label for="bio">Bio</label>
        <textarea id="bio" v-model.trim="profile.bio" class="textarea" />
      </div>

      <button class="button" type="submit">Profil speichern</button>
    </form>

    <aside class="card">
      <h2>Session</h2>
      <p v-if="user" class="muted">Angemeldet als {{ user.display_name }}.</p>
      <p v-if="user" class="muted">Rolle: <strong>{{ user.role }}</strong></p>
      <p class="muted">Die Session wird beim Laden der geschützten Seiten über das Backend validiert.</p>
    </aside>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import MessageBox from '@/components/ui/MessageBox.vue'
import { useSession } from '@/composables/useSession'
import { profileService } from '@/services/profileService'

const { user } = useSession()
const message = ref('')
const profile = reactive({
  display_name: '',
  main_role: '',
  fleet: '',
  bio: '',
})

async function loadProfile() {
  try {
    Object.assign(profile, await profileService.getMe())
  } catch (error) {
    message.value = error.response?.data?.detail || 'Profil konnte nicht geladen werden.'
  }
}

async function saveProfile() {
  try {
    Object.assign(profile, await profileService.updateMe(profile))
    message.value = 'Profil wurde gespeichert.'
  } catch (error) {
    message.value = error.response?.data?.detail || 'Profil konnte nicht gespeichert werden.'
  }
}

onMounted(loadProfile)
</script>
