<template>
  <section class="hero">
    <div class="card">
      <span class="badge">MVP Blueprint</span>
      <h1 class="hero-title">Plane deine WoSB-Gruppen schneller.</h1>
      <p class="hero-copy">
        Anmeldung, Profil, Gruppen, Gruppenverwaltung und Builds sind jetzt an eine serverseitig validierte Session
        gebunden. Das Frontend zeigt Rechte nur an, das Backend entscheidet über Zugriff und Verwaltung.
      </p>
      <div class="actions">
        <RouterLink v-if="isAuthenticated" class="button" to="/groups">Gruppen ansehen</RouterLink>
        <RouterLink v-if="isAuthenticated" class="button secondary" to="/builds">Builds öffnen</RouterLink>
        <RouterLink v-if="!isAuthenticated" class="button" to="/login">Anmelden</RouterLink>
        <RouterLink v-if="!isAuthenticated" class="button secondary" to="/register">Account erstellen</RouterLink>
      </div>
    </div>

    <aside class="card">
      <h2>Rechte & Rollen</h2>
      <div class="stat-list">
        <div class="stat"><strong>Public</strong><span class="muted">Home, Anmeldung und Registrierung</span></div>
        <div class="stat"><strong>Member</strong><span class="muted">Gruppen, Builds und eigenes Profil</span></div>
        <div class="stat"><strong>Admin</strong><span class="muted">eigener Admin-Bereich für alle Gruppen</span></div>
      </div>
    </aside>
  </section>
</template>

<script setup>
import { useSession } from '@/composables/useSession'

const { isAuthenticated } = useSession()
</script>
