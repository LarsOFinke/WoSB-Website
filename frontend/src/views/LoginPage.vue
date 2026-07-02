<template>
  <section class="card form-card">
    <h1>Anmelden</h1>
    <MessageBox :message="message" />

    <form @submit.prevent="login">
      <div class="form-row">
        <label for="username">Benutzername</label>
        <input id="username" v-model.trim="username" class="input" autocomplete="username" required />
      </div>

      <div class="form-row">
        <label for="password">Passwort</label>
        <input id="password" v-model.trim="password" class="input" type="password" autocomplete="current-password" required />
      </div>

      <div class="actions compact-actions">
        <button class="button" type="submit">Einloggen</button>
        <button class="button secondary" type="button" @click="fillDemoAdmin">Demo-Admin</button>
        <button class="button secondary" type="button" @click="fillDemoMember">Demo-Member</button>
      </div>
    </form>

    <p class="muted">Noch kein Account? <RouterLink class="text-link" to="/register">Jetzt registrieren</RouterLink>.</p>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import MessageBox from '@/components/ui/MessageBox.vue'
import { useSession } from '@/composables/useSession'
import { authService } from '@/services/authService'

const route = useRoute()
const router = useRouter()
const { setSession } = useSession()

const username = ref('demo')
const password = ref('demo123')
const message = ref('')

function fillDemoAdmin() {
  username.value = 'demo'
  password.value = 'demo123'
}

function fillDemoMember() {
  username.value = 'captain'
  password.value = 'captain123'
}

async function login() {
  message.value = 'Anmeldung läuft ...'
  try {
    const authResponse = await authService.login(username.value, password.value)
    setSession(authResponse)
    router.push(route.query.redirect || '/groups')
  } catch (error) {
    message.value = error.response?.data?.detail || 'Anmeldung fehlgeschlagen.'
  }
}
</script>
