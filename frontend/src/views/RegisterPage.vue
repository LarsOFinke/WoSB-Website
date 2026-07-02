<template>
  <section class="card form-card">
    <h1>Registrieren</h1>
    <MessageBox :message="message" />

    <form @submit.prevent="register">
      <div class="form-row">
        <label for="displayName">Anzeigename</label>
        <input id="displayName" v-model.trim="displayName" class="input" autocomplete="name" />
      </div>

      <div class="form-row">
        <label for="username">Benutzername</label>
        <input id="username" v-model.trim="username" class="input" autocomplete="username" required />
      </div>

      <div class="form-row">
        <label for="password">Passwort</label>
        <input id="password" v-model.trim="password" class="input" type="password" autocomplete="new-password" required />
      </div>

      <div class="actions compact-actions">
        <button class="button" type="submit">Account erstellen</button>
        <RouterLink class="button secondary" to="/login">Zur Anmeldung</RouterLink>
      </div>
    </form>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import MessageBox from '@/components/ui/MessageBox.vue'
import { useSession } from '@/composables/useSession'
import { authService } from '@/services/authService'

const router = useRouter()
const { setSession } = useSession()

const displayName = ref('')
const username = ref('')
const password = ref('')
const message = ref('')

async function register() {
  message.value = 'Registrierung läuft ...'
  try {
    const authResponse = await authService.register({
      username: username.value,
      password: password.value,
      display_name: displayName.value || username.value,
    })
    setSession(authResponse)
    router.push('/profile')
  } catch (error) {
    message.value = error.response?.data?.detail || 'Registrierung fehlgeschlagen.'
  }
}
</script>
