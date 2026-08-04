package eu.royalblackwater.api.builds;

import eu.royalblackwater.api.contract.ShipRead;
import java.util.Map;

record BuildShipSnapshot(
        ShipRead read,
        int upgradeSlots,
        int crewCapacity,
        int sailorMinimum,
        boolean hasLantern,
        Map<String, WeaponMount> mounts,
        MortarModification mortarModification,
        Map<String, Number> baseStats) {

    int capacity(String slot, boolean modified) {
        WeaponMount mount = mounts.get(slot);
        int capacity = mount == null ? 0 : mount.capacity();
        if (!modified || mortarModification == null) return capacity;
        if ("weapon_mortar".equals(slot)) return capacity + mortarModification.mortarCapacity();
        if ("weapon_port".equals(slot) || "weapon_starboard".equals(slot)) {
            return Math.max(0, capacity + mortarModification.broadsideCapacityDelta());
        }
        return capacity;
    }

    Double mortarCaliber(boolean modified) {
        WeaponMount mount = mounts.get("weapon_mortar");
        Double base = mount == null ? null : mount.maxCaliber();
        if (!modified || mortarModification == null) return base;
        return Math.max(base == null ? 0 : base, mortarModification.maxCaliber());
    }

    int specialCapacity(String slot) {
        WeaponMount mount = mounts.get(slot);
        return mount == null ? 0 : mount.specialCapacity();
    }

    Map<String, Number> mortarEffects(boolean installed) {
        return installed && mortarModification != null ? mortarModification.effects() : Map.of();
    }

    record WeaponMount(int capacity, int specialCapacity, Integer maxClassRank, Double maxCaliber) { }
    record MortarModification(int mortarCapacity, double maxCaliber, int broadsideCapacityDelta,
                              Map<String, Number> effects) { }
}
