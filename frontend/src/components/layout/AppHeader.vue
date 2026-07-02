<template>
  <header class="site-bar">
    <div class="header-inner">
      <RouterLink to="/" class="brand" aria-label="WoSB Home">
        <span class="brand-title">WoSB Gruppenmanagement</span>
        <span class="brand-subtitle">Flotten, Gruppen, Builds</span>
      </RouterLink>

      <nav class="nav-links" aria-label="Hauptnavigation">
        <RouterLink class="nav-link" to="/">Home</RouterLink>
        <RouterLink class="nav-link" to="/groups">Gruppen</RouterLink>
        <RouterLink v-if="isAuthenticated" class="nav-link" to="/group-management">Gruppenverwaltung</RouterLink>
        <RouterLink class="nav-link" to="/builds">Builds</RouterLink>
        <RouterLink v-if="isAuthenticated" class="nav-link" to="/profile">Profil</RouterLink>
        <RouterLink v-if="isAdmin" class="nav-link admin-link" to="/admin">Admin</RouterLink>
        <RouterLink v-if="!isAuthenticated" class="nav-link" to="/login">Anmelden</RouterLink>
        <RouterLink v-if="!isAuthenticated" class="nav-link" to="/register">Registrieren</RouterLink>
        <span v-if="isAuthenticated && user" class="session-pill">{{ user.display_name }} · {{ user.role }}</span>
        <button v-if="isAuthenticated" class="link-button" type="button" @click="logout">Abmelden</button>
      </nav>
    </div>
  </header>
</template>

<script setup>
import { useRouter } from 'vue-router'

import { useSession } from '@/composables/useSession'

const router = useRouter()
const { user, isAdmin, isAuthenticated, clearSession } = useSession()

function logout() {
  clearSession()
  router.push('/')
}
</script>
