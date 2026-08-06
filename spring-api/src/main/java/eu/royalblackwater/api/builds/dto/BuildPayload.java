package eu.royalblackwater.api.builds.dto;

import eu.royalblackwater.api.dto.BuildCreate;
import eu.royalblackwater.api.dto.BuildUpdate;
import eu.royalblackwater.api.dto.InventorySlot;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

public record BuildPayload(
        String name,
        String type,
        long shipId,
        List<String> classifications,
        String sails,
        List<String> upgrades,
        String lantern,
        boolean researchSlot,
        boolean mortarModification,
        long sailors,
        long soldiers,
        long musketeers,
        long mercenaries,
        List<InventorySlot> frontWeapons,
        List<InventorySlot> rearWeapons,
        List<InventorySlot> portWeapons,
        List<InventorySlot> starboardWeapons,
        List<InventorySlot> mortarWeapons,
        List<InventorySlot> specialWeapons,
        List<InventorySlot> specialCrew,
        List<InventorySlot> ammunition,
        List<InventorySlot> consumables,
        List<InventorySlot> hold,
        String details) {

    private static final Set<String> CLASSIFICATIONS = Set.of(
            "port_battle", "pve_solo", "pve_group", "pve_instanced", "pvp_solo", "pvp_group",
            "pvp_instanced", "trading", "fast", "combat", "heavy", "transport", "siege", "imperial");

    public static BuildPayload from(BuildCreate value) {
        return create(value.buildName(), value.buildType(), value.shipId(), value.classificationTags(), value.sails(),
                java.util.Arrays.asList(value.upgrade1(), value.upgrade2(), value.upgrade3(), value.upgrade4(), value.upgrade5(),
                        value.upgrade6(), value.upgrade7(), value.upgrade8()), value.lantern(),
                value.researchUpgradeSlotUnlocked(), value.mortarModificationInstalled(), value.sailors(),
                value.soldiers(), value.musketeers(), value.mercenaries(), value.frontWeaponSlots(),
                value.rearWeaponSlots(), value.portWeaponSlots(), value.starboardWeaponSlots(),
                value.mortarWeaponSlots(), value.specialWeaponSlots(), value.specialCrewSlots(),
                value.ammunitionSlots(), value.consumableSlots(), value.holdSlots(), value.details());
    }

    public static BuildPayload from(BuildUpdate value) {
        return create(value.buildName(), value.buildType(), value.shipId(), value.classificationTags(), value.sails(),
                java.util.Arrays.asList(value.upgrade1(), value.upgrade2(), value.upgrade3(), value.upgrade4(), value.upgrade5(),
                        value.upgrade6(), value.upgrade7(), value.upgrade8()), value.lantern(),
                value.researchUpgradeSlotUnlocked(), value.mortarModificationInstalled(), value.sailors(),
                value.soldiers(), value.musketeers(), value.mercenaries(), value.frontWeaponSlots(),
                value.rearWeaponSlots(), value.portWeaponSlots(), value.starboardWeaponSlots(),
                value.mortarWeaponSlots(), value.specialWeaponSlots(), value.specialCrewSlots(),
                value.ammunitionSlots(), value.consumableSlots(), value.holdSlots(), value.details());
    }

    private static BuildPayload create(String name, String type, long shipId, List<String> classifications,
                                       String sails, List<String> upgrades, String lantern, Boolean researchSlot,
                                       Boolean mortarModification, Long sailors, Long soldiers, Long musketeers,
                                       Long mercenaries, List<InventorySlot> front, List<InventorySlot> rear,
                                       List<InventorySlot> port, List<InventorySlot> starboard,
                                       List<InventorySlot> mortar, List<InventorySlot> special,
                                       List<InventorySlot> crew, List<InventorySlot> ammunition,
                                       List<InventorySlot> consumables, List<InventorySlot> hold, String details) {
        String normalizedName = required(name, "Build name", 140);
        String normalizedType = optional(type) == null ? "balanced" : optional(type).toLowerCase(Locale.ROOT);
        if (!normalizedType.matches("[a-z0-9][a-z0-9_-]{0,31}")) {
            throw new IllegalArgumentException("Invalid build role.");
        }
        LinkedHashSet<String> normalizedClassifications = new LinkedHashSet<>();
        for (String classification : list(classifications)) {
            String normalized = optional(classification);
            if (normalized == null) continue;
            normalized = normalized.toLowerCase(Locale.ROOT);
            if (!CLASSIFICATIONS.contains(normalized)) {
                throw new IllegalArgumentException("Invalid build classification: " + normalized + ".");
            }
            normalizedClassifications.add(normalized);
        }
        if (normalizedClassifications.size() > 6) {
            throw new IllegalArgumentException("A build can have at most 6 classifications.");
        }
        List<String> normalizedUpgrades = new ArrayList<>(8);
        for (String upgrade : upgrades) normalizedUpgrades.add(optional(upgrade));
        return new BuildPayload(normalizedName, normalizedType, shipId, List.copyOf(normalizedClassifications),
                optional(sails), Collections.unmodifiableList(normalizedUpgrades), optional(lantern),
                Boolean.TRUE.equals(researchSlot),
                Boolean.TRUE.equals(mortarModification), nonNegative(sailors), nonNegative(soldiers),
                nonNegative(musketeers), nonNegative(mercenaries), slots(front), slots(rear), slots(port),
                slots(starboard), slots(mortar), slots(special), uniqueSpecialists(crew), slots(ammunition),
                slots(consumables), slots(hold), boundedOptional(details, 3000));
    }

    public List<InventorySlot> slots(String slotType) {
        return switch (slotType) {
            case "weapon_front" -> frontWeapons;
            case "weapon_rear" -> rearWeapons;
            case "weapon_port" -> portWeapons;
            case "weapon_starboard" -> starboardWeapons;
            case "weapon_mortar" -> mortarWeapons;
            case "weapon_special" -> specialWeapons;
            case "special_crew" -> specialCrew;
            case "ammunition" -> ammunition;
            case "consumable" -> consumables;
            case "hold" -> hold;
            default -> List.of();
        };
    }

    private static List<InventorySlot> slots(List<InventorySlot> values) {
        List<InventorySlot> result = new ArrayList<>();
        for (InventorySlot value : list(values)) {
            if (value == null || optional(value.item()) == null) continue;
            result.add(new InventorySlot(optional(value.item()), value.quantity() == null ? 1L : Math.max(1L, value.quantity())));
        }
        return List.copyOf(result);
    }

    private static List<InventorySlot> uniqueSpecialists(List<InventorySlot> values) {
        LinkedHashSet<String> seen = new LinkedHashSet<>();
        List<InventorySlot> result = new ArrayList<>();
        for (InventorySlot slot : slots(values)) {
            if (seen.add(slot.item().toLowerCase(Locale.ROOT))) result.add(new InventorySlot(slot.item(), 1L));
        }
        return List.copyOf(result);
    }

    private static long nonNegative(Long value) { return value == null ? 0 : Math.max(0, value); }
    private static String required(String value, String label, int limit) {
        String normalized = optional(value);
        if (normalized == null) throw new IllegalArgumentException(label + " is required.");
        if (normalized.length() > limit) throw new IllegalArgumentException(label + " is too long.");
        return normalized;
    }
    private static String boundedOptional(String value, int limit) {
        String normalized = optional(value);
        if (normalized != null && normalized.length() > limit) throw new IllegalArgumentException("Details are too long.");
        return normalized;
    }
    private static String optional(String value) {
        if (value == null) return null;
        String normalized = value.strip();
        return normalized.isEmpty() ? null : normalized;
    }
    private static <T> List<T> list(List<T> value) { return value == null ? List.of() : value; }
}
