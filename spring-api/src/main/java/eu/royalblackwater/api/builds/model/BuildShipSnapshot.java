package eu.royalblackwater.api.builds.model;

import eu.royalblackwater.api.dto.ShipRead;
import java.util.Map;

public record BuildShipSnapshot(
        ShipRead read,
        int upgradeSlots,
        int crewCapacity,
        int sailorMinimum,
        boolean hasLantern,
        Map<String, WeaponMount> mounts,
        MortarModification mortarModification,
        Map<String, Number> baseStats) {

    public int capacity(String slot, boolean modified) {
        WeaponMount mount = mounts.get(slot);
        int capacity = mount == null ? 0 : mount.capacity();
        if (!modified || mortarModification == null) return capacity;
        if ("weapon_mortar".equals(slot)) return capacity + mortarModification.mortarCapacity();
        if ("weapon_port".equals(slot) || "weapon_starboard".equals(slot)) {
            return Math.max(0, capacity + mortarModification.broadsideCapacityDelta());
        }
        return capacity;
    }

    public Double mortarCaliber(boolean modified) {
        WeaponMount mount = mounts.get("weapon_mortar");
        Double base = mount == null ? null : mount.maxCaliber();
        if (!modified || mortarModification == null) return base;
        return Math.max(base == null ? 0 : base, mortarModification.maxCaliber());
    }

    public int specialCapacity(String slot) {
        WeaponMount mount = mounts.get(slot);
        return mount == null ? 0 : mount.specialCapacity();
    }

    public Map<String, Number> mortarEffects(boolean installed) {
        return installed && mortarModification != null ? mortarModification.effects() : Map.of();
    }

    public record WeaponMount(int capacity, int specialCapacity, Integer maxClassRank, Double maxCaliber) { }
    public record MortarModification(int mortarCapacity, double maxCaliber, int broadsideCapacityDelta,
                              Map<String, Number> effects) { }
}
