<script setup>
import { useLocale } from '@/locales'
const props = defineProps({ selectedObject: { type: Object, required: true }, ships: { type: Array, required: true }, guides: { type: Array, required: true }, selectedBuilds: { type: Array, required: true }, colors: { type: Array, required: true } })
const emit = defineEmits(['update-selected-ship', 'record-history', 'delete-selected'])
const { t } = useLocale()
function setColor(value) { props.selectedObject.color = value; emit('record-history') }
</script>
<template>
  <section class="strategy-panel strategy-selection-panel">
    <label v-if="selectedObject.type === 'ship'"><span>{{ t('strategyPlanner.ship') }}</span><select v-model.number="selectedObject.shipId" required @change="emit('update-selected-ship')"><option value="">—</option><option v-for="ship in ships" :key="ship.id" :value="ship.id">{{ ship.name }} · {{ ship.ship_type }} · R{{ ship.rate }}</option></select></label>
    <div v-if="selectedObject.type === 'ship'" class="strategy-field-pair"><label><span>{{ t('strategyPlanner.shipName') }}</span><input v-model="selectedObject.shipName" maxlength="120" @change="emit('record-history')" /></label><label><span>{{ t('strategyPlanner.playerName') }}</span><input v-model="selectedObject.playerName" maxlength="120" @change="emit('record-history')" /></label></div>
    <label v-if="selectedObject.type === 'ship'"><span>{{ t('strategyPlanner.build') }}</span><select v-model="selectedObject.buildId" @change="emit('record-history')"><option :value="null">{{ t('strategyPlanner.noBuild') }}</option><option v-for="build in selectedBuilds" :key="build.id" :value="build.id">{{ build.build_name }}</option></select></label>
    <label v-if="selectedObject.type === 'ship'"><span>{{ t('strategyPlanner.guide') }}</span><select v-model="selectedObject.guideId" @change="emit('record-history')"><option :value="null">{{ t('strategyPlanner.noGuide') }}</option><option v-for="guide in guides" :key="guide.id" :value="guide.id">{{ guide.title }}</option></select></label>
    <label v-if="selectedObject.type === 'text'"><span>{{ t('strategyPlanner.textValue') }}</span><input v-model="selectedObject.text" maxlength="500" @change="emit('record-history')" /></label>
    <div v-if="selectedObject.type === 'text'" class="strategy-text-color-field"><label><span>{{ t('strategyPlanner.textColor') }}</span><input v-model="selectedObject.color" class="strategy-native-color" type="color" @change="emit('record-history')" /></label><div class="strategy-object-colors" :aria-label="t('strategyPlanner.textColor')"><button v-for="value in colors" :key="value" type="button" :class="{ active: selectedObject.color === value }" :style="{ '--strategy-color': value }" :aria-label="`${t('strategyPlanner.textColor')} ${value}`" :aria-pressed="selectedObject.color === value" @click="setColor(value)"><span v-if="selectedObject.color === value" aria-hidden="true">✓</span></button></div></div>
    <button class="danger-action" type="button" @click="emit('delete-selected')">{{ t('strategyPlanner.deleteObject') }}</button>
  </section>
</template>
