export function effectObjectToRows(effects = {}) {
  return Object.entries(effects).map(([key, value]) => ({ key, value: Number(value) }))
}

export function effectRowsToObject(rows = []) {
  return Object.fromEntries(
    rows
      .filter((row) => row.key)
      .map((row) => [row.key, Number(row.value)]),
  )
}

export function availableEffectDefinitions(definitions, rows, rowIndex) {
  const currentKey = rows[rowIndex]?.key
  const selected = new Set(rows.map((row) => row.key).filter(Boolean))
  return definitions.filter((definition) => definition.key === currentKey || !selected.has(definition.key))
}

export function addEffectRow(rows, definitions) {
  const [definition] = availableEffectDefinitions(definitions, rows, -1)
  if (!definition) return rows
  return [...rows, { key: definition.key, value: definition.value_type === 'boolean' ? 1 : 0 }]
}
