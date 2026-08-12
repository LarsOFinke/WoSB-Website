<script setup>
defineProps({
  name: { type: String, required: true },
  size: { type: [String, Number], default: 20 },
  strokeWidth: { type: [String, Number], default: 1.8 },
})
</script>

<template>
  <svg
    class="app-icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <template v-if="name === 'home'">
      <path d="m3 10 9-7 9 7" />
      <path d="M5 9.5V21h14V9.5" />
      <path d="M9 21v-7h6v7" />
    </template>
    <template v-else-if="name === 'builds'">
      <path d="M12 3v3M12 18v3M3 12h3M18 12h3" />
      <path d="m5.6 5.6 2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1" />
      <circle cx="12" cy="12" r="4" />
    </template>
    <template v-else-if="name === 'guides'">
      <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H11v16H6.5A2.5 2.5 0 0 0 4 21.5z" />
      <path d="M20 5.5A2.5 2.5 0 0 0 17.5 3H13v16h4.5a2.5 2.5 0 0 1 2.5 2.5z" />
    </template>
    <template v-else-if="name === 'folder'">
      <path d="M3 6.5h6l2 2h10v9.5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      <path d="M3 10h18" />
    </template>
    <template v-else-if="name === 'groups'">
      <circle cx="8" cy="8" r="3" />
      <circle cx="17" cy="9" r="2.5" />
      <path d="M2.5 20a5.5 5.5 0 0 1 11 0" />
      <path d="M13 20a4.5 4.5 0 0 1 8.5-2" />
    </template>
    <template v-else-if="name === 'calendar'">
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M8 3v4M16 3v4M3 10h18" />
      <path d="M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01" />
    </template>
    <template v-else-if="name === 'forum'">
      <path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z" />
      <path d="M8 9h8M8 13h5" />
    </template>
    <template v-else-if="name === 'fleet'">
      <path d="M12 3v14" />
      <path d="M12 5 6 9h6M12 7l6 4h-6" />
      <path d="M4 17h16l-2 4H6z" />
    </template>
    <template v-else-if="name === 'shield'">
      <path d="M12 3 4.5 6v5.5c0 4.8 3 7.8 7.5 9.5 4.5-1.7 7.5-4.7 7.5-9.5V6z" />
      <path d="m9 12 2 2 4-4" />
    </template>
    <template v-else-if="name === 'user'">
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21a8 8 0 0 1 16 0" />
    </template>
    <template v-else-if="name === 'menu'">
      <path d="M4 7h16M4 12h16M4 17h16" />
    </template>
    <template v-else-if="name === 'chevron-left'">
      <path d="m15 18-6-6 6-6" />
    </template>
    <template v-else-if="name === 'chevron-right'">
      <path d="m9 18 6-6-6-6" />
    </template>
    <template v-else-if="name === 'close'">
      <path d="m6 6 12 12M18 6 6 18" />
    </template>
    <template v-else-if="name === 'logout'">
      <path d="M10 17l5-5-5-5M15 12H3" />
      <path d="M14 3h5a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-5" />
    </template>
    <template v-else-if="name === 'login'">
      <path d="m14 17 5-5-5-5M19 12H7" />
      <path d="M10 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h5" />
    </template>
    <template v-else-if="name === 'globe'">
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" />
    </template>
    <template v-else-if="name === 'arrow-right'">
      <path d="M5 12h14M13 6l6 6-6 6" />
    </template>
    <template v-else-if="name === 'activity'">
      <path d="M3 12h4l2.5-7 5 14 2.5-7h4" />
    </template>
    <template v-else-if="name === 'database'">
      <ellipse cx="12" cy="5" rx="8" ry="3" />
      <path d="M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5" />
      <path d="M4 12v7c0 1.7 3.6 3 8 3s8-1.3 8-3v-7" />
    </template>
    <template v-else-if="name === 'inbox'">
      <path d="M4 5h16v14H4z" />
      <path d="M4 14h4l2 3h4l2-3h4" />
    </template>
    <template v-else-if="name === 'lock'">
      <rect x="5" y="10" width="14" height="11" rx="2" />
      <path d="M8 10V7a4 4 0 0 1 8 0v3" />
    </template>
    <template v-else-if="name === 'users'">
      <circle cx="9" cy="8" r="3" />
      <path d="M3 20a6 6 0 0 1 12 0" />
      <path d="M16 5.5a3 3 0 0 1 0 5.5M17 14a5 5 0 0 1 4 5" />
    </template>
    <template v-else-if="name === 'spark'">
      <path d="m12 3 1.3 4.2L17.5 9l-4.2 1.3L12 15l-1.3-4.7L6.5 9l4.2-1.8z" />
      <path d="m18.5 14 .7 2.3 2.3.7-2.3.7-.7 2.3-.7-2.3-2.3-.7 2.3-.7z" />
    </template>
    <template v-else-if="name === 'webhook'">
      <path d="M7.5 8.5a4 4 0 1 1 3.8-5.2" />
      <path d="M16.5 15.5a4 4 0 1 1-3.8 5.2" />
      <path d="M8.5 16.5a4 4 0 1 1-5.2-3.8" />
      <path d="m9.5 7.5 5 9M7 16h10M14.5 7.5l-5 9" />
    </template>
    <template v-else-if="name === 'compass'">
      <circle cx="12" cy="12" r="9" />
      <path d="m15.5 8.5-2.2 4.8-4.8 2.2 2.2-4.8z" />
    </template>
    <template v-else-if="name === 'anchor'">
      <circle cx="12" cy="5" r="2.5" /><path d="M12 7.5V21M8 11h8M4 15a8 8 0 0 0 16 0M4 15l-2 2M20 15l2 2" />
    </template>
    <template v-else-if="name === 'swords' || name === 'duel'">
      <path d="m5 4 6 6-2 2-6-6V4zM19 4l-6 6 2 2 6-6V4zM7 14l-4 4 3 3 4-4M17 14l4 4-3 3-4-4" />
    </template>
    <template v-else-if="name === 'fort'">
      <path d="M4 21V9h4V5h3v4h2V5h3v4h4v12M8 21v-4h3v4M15 21v-4h3v4M3 21h18" />
    </template>
    <template v-else-if="name === 'trade'">
      <path d="M12 4v16M5 7h14M7 7l-4 7h8zM17 7l-4 7h8z" />
    </template>
    <template v-else-if="name === 'speed'">
      <path d="M4 8h9M2 12h12M5 16h8M17 7c3 1 4 3 4 5s-1 4-4 5" />
    </template>
    <template v-else-if="name === 'transport'">
      <path d="M3 7h11v10H3zM14 10h4l3 3v4h-7zM6 7V4h5v3M7 20a2 2 0 1 0 0-4 2 2 0 0 0 0 4M17 20a2 2 0 1 0 0-4 2 2 0 0 0 0 4" />
    </template>
    <template v-else-if="name === 'crown'">
      <path d="m4 8 4 4 4-7 4 7 4-4-2 10H6zM6 21h12" />
    </template>
    <template v-else-if="name === 'edit'">
      <path d="M4 20h4l11-11-4-4L4 16z" />
      <path d="m13.5 6.5 4 4" />
    </template>
    <template v-else>
      <circle cx="12" cy="12" r="8" />
    </template>
  </svg>
</template>
