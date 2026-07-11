export function sumEffects(...effectSets) {
  const totals = {}
  for (const effects of effectSets) {
    for (const [key, rawValue] of Object.entries(effects || {})) {
      totals[key] = (Number(totals[key]) || 0) + (Number(rawValue) || 0)
    }
  }
  return totals
}

export function calculateUpgradeSlotAccess({
  shipUpgradeSlots,
  unlockEffectSlots = 0,
  researchUpgradeSlotUnlocked = false,
  slotLimit = 6,
  baseSlotLimit = 4,
}) {
  const baseSlots = Math.min(Math.max(Number(shipUpgradeSlots) || 0, 0), baseSlotLimit)
  const effectSlots = Math.min(Math.max(Number(unlockEffectSlots) || 0, 0), slotLimit - baseSlots)
  const researchSlots = researchUpgradeSlotUnlocked ? 1 : 0
  const nonShipUnlocks = Math.min(effectSlots + researchSlots, slotLimit - baseSlots)
  const shipExtraSlots = Number(shipUpgradeSlots) >= slotLimit ? 1 : 0
  const slot5Unlocked = nonShipUnlocks >= 1
  const slot6Available = shipExtraSlots > 0 || nonShipUnlocks >= 2

  return {
    baseSlots,
    effectSlots,
    researchSlots,
    shipExtraSlots,
    slot5Unlocked,
    slot6Available,
    availableSlots: Math.min(slotLimit, baseSlots + Number(slot5Unlocked) + Number(slot6Available)),
  }
}
