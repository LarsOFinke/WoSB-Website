export function filterOptionGroups(groups, query) {
  const normalizedQuery = String(query || '').trim().toLocaleLowerCase()
  if (!normalizedQuery) return groups

  return (groups || [])
    .map((group) => ({
      ...group,
      options: (group.options || []).filter((option) => [option.label, option.meta, option.value]
        .filter(Boolean)
        .some((value) => String(value).toLocaleLowerCase().includes(normalizedQuery))),
    }))
    .filter((group) => group.options.length > 0)
}
