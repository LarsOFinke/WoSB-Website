import { watch } from 'vue'

import { crewSliderMax, normalizeCrewAllocation, setCrewAllocationValue } from '@/modules/builds/crewAllocation'

export function useBuildCrew({ form, crewCapacity, sailorMinimum }) {
  function currentCrewAllocation() {
    return {
      sailors: form.sailors,
      musketeers: form.musketeers,
      soldiers: form.soldiers,
      mercenaries: form.mercenaries,
    }
  }

  function applyCrewAllocation(allocation) {
    Object.assign(form, allocation)
  }

  function crewMaxFor(fieldName) {
    return crewSliderMax(currentCrewAllocation(), fieldName, crewCapacity.value, sailorMinimum.value)
  }

  function onCrewSliderInput(fieldName, event) {
    applyCrewAllocation(setCrewAllocationValue(
      currentCrewAllocation(),
      fieldName,
      event.target.value,
      crewCapacity.value,
      sailorMinimum.value,
    ))
  }

  function normalizeCurrentCrew() {
    applyCrewAllocation(normalizeCrewAllocation(currentCrewAllocation(), crewCapacity.value, sailorMinimum.value))
  }

  function resetCrewAllocation() {
    applyCrewAllocation(normalizeCrewAllocation({ sailors: 0 }, crewCapacity.value, sailorMinimum.value))
  }

  watch([crewCapacity, sailorMinimum], normalizeCurrentCrew)

  return { crewMaxFor, onCrewSliderInput, normalizeCurrentCrew, resetCrewAllocation }
}
