<script setup>
import { useLocale } from '@/locales'
const props = defineProps({ marker: { type: Object, required: true }, ships: { type: Array, required: true }, guides: { type: Array, required: true }, markerBuilds: { type: Array, required: true } })
const emit = defineEmits(['update-marker-ship', 'add-ship'])
const { t } = useLocale()
</script>
<template>
  <section class="strategy-panel strategy-marker-panel">
    <label><span>{{ t('strategyPlanner.ship') }}</span><select v-model="marker.shipId" required @change="emit('update-marker-ship')"><option value="">—</option><option v-for="ship in ships" :key="ship.id" :value="ship.id">{{ ship.name }} · {{ ship.ship_type }} · R{{ ship.rate }}</option></select></label>
    <div class="strategy-field-pair"><label><span>{{ t('strategyPlanner.shipName') }}</span><input v-model="marker.shipName" maxlength="120" /></label><label><span>{{ t('strategyPlanner.playerName') }}</span><input v-model="marker.playerName" maxlength="120" /></label></div>
    <label><span>{{ t('strategyPlanner.build') }}</span><select v-model="marker.buildId" :disabled="!marker.shipId"><option value="">{{ t('strategyPlanner.noBuild') }}</option><option v-for="build in markerBuilds" :key="build.id" :value="build.id">{{ build.build_name }}</option></select></label>
    <label><span>{{ t('strategyPlanner.guide') }}</span><select v-model="marker.guideId"><option value="">{{ t('strategyPlanner.noGuide') }}</option><option v-for="guide in guides" :key="guide.id" :value="guide.id">{{ guide.title }}</option></select></label>
    <button class="primary-action strategy-add-marker" type="button" @click="emit('add-ship')">{{ t('strategyPlanner.addMarker') }}</button>
  </section>
</template>
