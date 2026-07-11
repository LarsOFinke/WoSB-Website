<script setup>
const props = defineProps({
  date: { type: String, default: '' },
  time: { type: String, default: '' },
  dateLabel: { type: String, required: true },
  timeLabel: { type: String, required: true },
  dateRequired: { type: Boolean, default: false },
  timeRequired: { type: Boolean, default: false },
  showTime: { type: Boolean, default: true },
  minDate: { type: String, default: '2000-01-01' },
  maxDate: { type: String, default: '2100-12-31' },
})

const emit = defineEmits(['update:date', 'update:time'])

function updateDate(event) {
  emit('update:date', event.target.value)
}

function updateTime(event) {
  emit('update:time', event.target.value)
}
</script>

<template>
  <div class="local-date-time-fields" :class="{ 'date-only': !showTime }">
    <label class="field-stack local-date-field">
      <span class="field-label">{{ dateLabel }}</span>
      <span class="input-panel embedded-field date-input-shell">
        <input
          :value="props.date"
          type="date"
          :required="dateRequired"
          :min="minDate"
          :max="maxDate"
          autocomplete="off"
          @input="updateDate"
        />
      </span>
    </label>
    <label v-if="showTime" class="field-stack local-time-field">
      <span class="field-label">{{ timeLabel }}</span>
      <span class="input-panel embedded-field time-input-shell">
        <input
          :value="props.time"
          type="time"
          :required="timeRequired"
          step="60"
          autocomplete="off"
          @input="updateTime"
        />
      </span>
    </label>
  </div>
</template>
