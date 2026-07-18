export const BUILD_DISCOVERY_GROUPS = Object.freeze([
  {
    key: 'useCase',
    values: [
      ['port_battle', 'anchor', 'harbor'],
      ['pve_solo', 'swords', 'sea'],
      ['pve_group', 'groups', 'sea'],
      ['pve_instanced', 'fort', 'sea'],
      ['pvp_solo', 'duel', 'battle'],
      ['pvp_group', 'fleet', 'battle'],
      ['pvp_instanced', 'shield', 'battle'],
    ],
  },
  {
    key: 'role',
    values: [
      ['trading', 'trade', 'trade'],
      ['fast', 'speed', 'sea'],
      ['combat', 'builds', 'battle'],
      ['heavy', 'shield', 'iron'],
      ['transport', 'transport', 'trade'],
      ['siege', 'fort', 'battle'],
      ['imperial', 'crown', 'harbor'],
    ],
  },
])

export const BUILD_DISCOVERY_VALUES = Object.freeze(
  BUILD_DISCOVERY_GROUPS.flatMap((group) => group.values.map(([value]) => value)),
)

export function localizedBuildDiscoveryGroups(t) {
  return BUILD_DISCOVERY_GROUPS.map((group) => ({
    key: group.key,
    label: t(`discovery.builds.groups.${group.key}`),
    items: group.values.map(([value, icon, tone]) => ({
      value,
      icon,
      tone,
      label: t(`discovery.builds.tags.${value}.label`),
      description: t(`discovery.builds.tags.${value}.description`),
    })),
  }))
}
