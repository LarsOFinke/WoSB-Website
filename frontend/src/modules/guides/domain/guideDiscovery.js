export const GUIDE_DISCOVERY_GROUPS = Object.freeze([
  { key: 'start', values: [['new_captains', 'compass'], ['general', 'guides']] },
  { key: 'combat', values: [['builds', 'builds'], ['pve', 'shield'], ['pvp', 'swords'], ['port_battles', 'fort']] },
  { key: 'fleet', values: [['fleet_operations', 'fleet'], ['economy', 'trade']] },
])

export const GUIDE_CATEGORY_VALUES = Object.freeze(
  GUIDE_DISCOVERY_GROUPS.flatMap((group) => group.values.map(([value]) => value)),
)

export function localizedGuideDiscoveryGroups(t) {
  return GUIDE_DISCOVERY_GROUPS.map((group) => ({
    key: group.key,
    label: t(`discovery.guides.groups.${group.key}`),
    items: group.values.map(([value, icon]) => ({
      value,
      icon,
      tone: group.key === 'combat' ? 'battle' : group.key === 'fleet' ? 'trade' : 'sea',
      label: t(`guides.categories.${value}`),
      description: t(`discovery.guides.categories.${value}`),
    })),
  }))
}

export function localizedGuideCategoryItems(t) {
  return localizedGuideDiscoveryGroups(t).flatMap((group) => group.items)
}
