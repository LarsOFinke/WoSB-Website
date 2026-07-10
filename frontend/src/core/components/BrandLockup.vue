<script setup>
import { useLocale } from '@/locales'

defineProps({
  compact: { type: Boolean, default: false },
})

const { t } = useLocale()
const brandIconSrc = '/branding/rbf-fleet-icon.png'
</script>

<template>
  <span class="brand-lockup" :class="{ 'is-compact': compact }">
    <span class="brand-mark" aria-hidden="true">
      <img class="brand-mark-image" :src="brandIconSrc" alt="" loading="eager" decoding="async" />
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
