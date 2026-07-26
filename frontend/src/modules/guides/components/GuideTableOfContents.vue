<script setup>
import AppIcon from '@/core/components/AppIcon.vue'
import { useLocale } from '@/locales'

defineProps({
  headings: { type: Array, required: true },
})

const { t } = useLocale()
</script>

<template>
  <nav v-if="headings.length" class="guide-contents" :aria-label="t('guides.print.contentsTitle')">
    <div class="guide-contents-heading">
      <AppIcon name="guides" :size="18" />
      <strong>{{ t('guides.print.contentsTitle') }}</strong>
    </div>
    <ol>
      <li v-for="heading in headings" :key="heading.id" :class="`level-${heading.level}`">
        <a :href="`#${heading.id}`">
          <span>{{ heading.number }}</span>
          {{ heading.label }}
        </a>
      </li>
    </ol>
  </nav>
</template>
