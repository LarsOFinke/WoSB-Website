<script setup>
defineProps({
  t: { type: Function, required: true },
  form: { type: Object, required: true },
  buildCrewVisuals: { type: Object, required: true },
  crewInvalid: { type: Boolean, required: true },
  crewTotal: { type: Number, required: true },
  crewCapacity: { type: Number, required: true },
  crewRemaining: { type: Number, required: true },
  sailorMinimum: { type: Number, required: true },
  sailingEfficiency: { type: Number, required: true },
  sailorsBelowMinimum: { type: Boolean, required: true },
  crewOverLimit: { type: Boolean, required: true },
  crewMaxFor: { type: Function, required: true },
  onCrewSliderInput: { type: Function, required: true },
})
</script>

<template>
  <section class="wire-section form-section crew-section compact-crew-panel" :aria-label="t('builds.create.sections.crew')">
    <div class="section-title">
      <span>05</span>
      <h2>{{ t('builds.create.sections.crew') }}</h2>
    </div>
    <div class="crew-allocation-console" :class="{ 'is-invalid': crewInvalid }">
      <div class="crew-allocation-header">
        <div>
          <span>{{ t('builds.crewConsole.eyebrow') }}</span>
          <strong>{{ t('builds.crewConsole.title') }}</strong>
        </div>
        <div class="crew-allocation-total">
          <strong>{{ crewTotal }}/{{ crewCapacity || '—' }}</strong>
          <span>{{ t('builds.create.crew.free', { value: crewRemaining }) }}</span>
        </div>
      </div>
      <div class="crew-allocation-meter" :aria-label="t('builds.create.crew.total', { current: crewTotal, max: crewCapacity || '—' })">
        <span class="crew-meter-sailors" :style="{ width: `${crewCapacity ? (Number(form.sailors) / crewCapacity) * 100 : 0}%` }"></span>
        <span class="crew-meter-musketeers" :style="{ width: `${crewCapacity ? (Number(form.musketeers) / crewCapacity) * 100 : 0}%` }"></span>
        <span class="crew-meter-soldiers" :style="{ width: `${crewCapacity ? (Number(form.soldiers) / crewCapacity) * 100 : 0}%` }"></span>
        <span class="crew-meter-mercenaries" :style="{ width: `${crewCapacity ? (Number(form.mercenaries) / crewCapacity) * 100 : 0}%` }"></span>
      </div>
      <div class="crew-allocation-legend">
        <span>{{ t('builds.create.crew.sailorMinimum', { value: sailorMinimum }) }}</span>
        <span>{{ t('builds.crewConsole.dynamicLimit') }}</span>
        <span>{{ t('builds.create.crew.workingSpeed', { value: sailingEfficiency }) }}</span>
        <span v-if="sailorsBelowMinimum" class="crew-warning">{{ t('builds.create.crew.tooFewSailors', { current: form.sailors, minimum: sailorMinimum }) }}</span>
        <span v-if="crewOverLimit" class="crew-warning">{{ t('builds.create.crew.tooManyCrew') }}</span>
      </div>

      <div class="crew-grid section-fields">
        <label v-for="role in ['sailors', 'musketeers', 'soldiers', 'mercenaries']" :key="role" class="crew-slider-card" :class="`crew-${role}`">
          <img class="crew-role-image" :src="buildCrewVisuals[role]" alt="" />
          <span><small>{{ t(`builds.create.crew.${role}`) }}</small><strong>{{ form[role] }}</strong></span>
          <input :value="form[role]" type="range" min="0" :max="crewMaxFor(role)" @input="onCrewSliderInput(role, $event)" />
          <small>0–{{ crewMaxFor(role) }}</small>
        </label>
      </div>
    </div>
  </section>
</template>
