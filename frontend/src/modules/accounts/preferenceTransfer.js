export function normalizePreferenceIds(values) {
  return [...new Set((values || [])
    .map((value) => Number(value))
    .filter((value) => Number.isInteger(value) && value > 0))]
}

export function addPreferenceId(values, id) {
  const normalized = normalizePreferenceIds(values)
  const candidate = Number(id)
  if (!Number.isInteger(candidate) || candidate <= 0 || normalized.includes(candidate)) return normalized
  return [...normalized, candidate]
}

export function removePreferenceId(values, id) {
  const candidate = Number(id)
  return normalizePreferenceIds(values).filter((value) => value !== candidate)
}

export function splitPreferenceOptions(options, selectedValues) {
  const selectedIds = normalizePreferenceIds(selectedValues)
  const selectedSet = new Set(selectedIds)
  const optionById = new Map((options || []).map((option) => [Number(option.id), option]))
  return {
    selectedIds,
    availableOptions: (options || []).filter((option) => !selectedSet.has(Number(option.id))),
    selectedOptions: selectedIds.map((id) => optionById.get(id)).filter(Boolean),
  }
}
