<script setup>
import { useLocale } from '@/locales'

defineProps({
  compact: { type: Boolean, default: false },
})

const { t } = useLocale()
</script>

<template>
  <span class="brand-lockup" :class="{ 'is-compact': compact }">
    <span class="brand-mark" aria-hidden="true">
      <span>RBV</span>
    </span>
    <span class="brand-copy">
      <strong>
        <span>{{ t('common.brandLineOne') }}</span>
        <span>{{ t('common.brandLineTwo') }}</span>
      </strong>
      <small>{{ t('common.brandDescriptor') }}</small>
    </span>
  </span>
</template>
