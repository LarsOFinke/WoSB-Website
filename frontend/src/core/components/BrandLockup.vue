<script setup>
import fleetIconUrl from '@/assets/rbf-fleet-icon.png'
import { useLocale } from '@/locales'

defineProps({
  compact: { type: Boolean, default: false },
})

const { t } = useLocale()
</script>

<template>
  <span class="brand-lockup" :class="{ 'is-compact': compact }">
    <span class="brand-mark" aria-hidden="true">
      <img class="brand-mark-image" :src="fleetIconUrl" alt="" loading="eager" decoding="async" />
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
