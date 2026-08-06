package eu.royalblackwater.api.builds.service;

import eu.royalblackwater.api.builds.mapper.BuildDtoMapper;
import eu.royalblackwater.api.builds.model.BuildEffects;
import eu.royalblackwater.api.builds.model.BuildFeatureSnapshot;
import eu.royalblackwater.api.builds.model.BuildPayload;
import eu.royalblackwater.api.builds.model.BuildShipSnapshot;
import eu.royalblackwater.api.builds.model.BuildSlotSelection;
import eu.royalblackwater.api.builds.model.UpgradeSlotAccess;
import eu.royalblackwater.api.dto.BuildStatRow;
import eu.royalblackwater.api.dto.ShipStats;
import eu.royalblackwater.api.shared.mapper.ContractConversionService;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;

@Service
public class BuildStatsService {
    private static final Set<String> DEBUFF_KEYS = Set.of(
            "speed_pct", "turn_rate_pct", "crew_capacity", "hull_hp_pct", "reload_pct",
            "weapon_range_pct", "boarding_power_pct");
    private final BuildEffectService effects;
    private final UpgradeSlotService upgradeSlots;
    private final BuildStatCalculator calculator;
    private final ContractConversionService contracts;

    public BuildStatsService(BuildEffectService effects, UpgradeSlotService upgradeSlots,
                      BuildStatCalculator calculator, ContractConversionService contracts) {
        this.effects = effects;
        this.upgradeSlots = upgradeSlots;
        this.calculator = calculator;
        this.contracts = contracts;
    }

    public ShipStats calculate(BuildPayload payload, BuildShipSnapshot ship, BuildFeatureSnapshot feature,
                        List<BuildSlotSelection> slots) {
        BuildEffects resolved = effects.resolve(payload, ship, feature, slots);
        UpgradeSlotAccess access = upgradeSlots.calculate(ship, feature, slots);
        List<BuildStatRow> statRows = calculator.calculate(ship.baseStats(), resolved.totals(), resolved.sets());
        long crewTotal = payload.sailors() + payload.soldiers() + payload.musketeers() + payload.mercenaries();
        long crewCapacity = effectiveCrewCapacity(ship, resolved);
        long sailorMinimum = Math.max(0, ship.sailorMinimum() + integer(resolved.totals().get("sailor_minimum")));
        long sailingEfficiency = sailorMinimum <= 0 ? 100
                : Math.min(100, Math.max(0, BuildStatCalculator.roundWhole(payload.sailors() * 100.0 / sailorMinimum)));
        Map<String, Long> weaponSlots = new LinkedHashMap<>();
        Map<String, Long> weaponCapacity = new LinkedHashMap<>();
        for (Map.Entry<String, String> arc : Map.of(
                "front", "weapon_front", "rear", "weapon_rear", "port", "weapon_port",
                "starboard", "weapon_starboard", "mortar", "weapon_mortar", "special", "weapon_special").entrySet()) {
            weaponSlots.put(arc.getKey(), slots.stream().filter(slot -> slot.type().equals(arc.getValue()))
                    .mapToLong(BuildSlotSelection::quantity).sum());
            weaponCapacity.put(arc.getKey(), (long) ship.capacity(arc.getValue(), payload.mortarModification()));
        }
        Map<String, Number> sailEffects = effectsFor(slots, "sail");
        Map<String, Number> lanternEffects = effectsFor(slots, "lantern");
        Map<String, Number> upgradeEffects = effectsFor(slots, "upgrade");
        Map<String, Number> specialistEffects = specialistEffects(payload, ship, feature, slots, resolved);
        Map<String, Number> debuffs = new LinkedHashMap<>();
        Map<String, Number> buffs = new LinkedHashMap<>();
        resolved.totals().forEach((key, value) -> {
            if (value.doubleValue() < 0 || key.startsWith("debuff_") || DEBUFF_KEYS.contains(key) && value.doubleValue() < 0) {
                debuffs.put(key, value);
            } else if (!"extra_upgrade_slots".equals(key)) buffs.put(key, value);
        });
        List<String> warnings = warnings(payload, crewCapacity, sailorMinimum, access);
        long upgradeUsed = slots.stream().filter(slot -> slot.type().equals("upgrade")).count();
        long ammunition = countRows(slots, "ammunition");
        long consumables = countRows(slots, "consumable");
        long hold = countRows(slots, "hold");
        Map<String, Object> value = new LinkedHashMap<>();
        value.put("crew_total", crewTotal); value.put("crew_capacity", crewCapacity);
        value.put("crew_remaining", Math.max(crewCapacity - crewTotal, 0));
        value.put("sailor_minimum", sailorMinimum); value.put("sailors_required_met", payload.sailors() >= sailorMinimum);
        value.put("sailor_target", sailorMinimum); value.put("base_sailor_target", (long) ship.sailorMinimum());
        value.put("effective_sailor_target", sailorMinimum); value.put("sailing_efficiency_pct", sailingEfficiency);
        value.put("upgrade_slots_used", upgradeUsed); value.put("upgrade_slots_available", (long) access.availableSlots());
        value.put("base_upgrade_slots_available", (long) access.baseSlots());
        value.put("extra_upgrade_slots", integer(upgradeEffects.get("extra_upgrade_slots")));
        value.put("expansion_upgrade_slots", (long) access.expansionSlots()); value.put("research_upgrade_slots", (long) access.researchSlots());
        value.put("ship_extra_upgrade_slots", (long) access.shipExtraSlots()); value.put("upgrade_slot_5_unlocked", access.slot5());
        value.put("upgrade_slot_6_available", access.slot6()); value.put("upgrade_slot_6_unlocked", access.slot6());
        value.put("upgrade_slot_7_available", access.slot7()); value.put("upgrade_slot_8_available", access.slot8());
        value.put("base_crew_capacity", (long) ship.crewCapacity()); value.put("effective_crew_capacity", crewCapacity);
        value.put("base_sailor_minimum", (long) ship.sailorMinimum()); value.put("effective_sailor_minimum", sailorMinimum);
        value.put("item_effects", resolved.totals()); value.put("sail_effects", sailEffects);
        value.put("lantern_effects", lanternEffects); value.put("upgrade_effects", upgradeEffects);
        value.put("special_crew_effects", specialistEffects);
        value.put("research_upgrade_slot_effects", feature == null ? Map.of() : feature.effects());
        value.put("mortar_modification_installed", payload.mortarModification());
        value.put("mortar_modification_effects", ship.mortarEffects(payload.mortarModification()));
        value.put("upgrade_buffs", Map.copyOf(buffs)); value.put("upgrade_debuffs", Map.copyOf(debuffs));
        value.put("base_stats", ship.baseStats()); value.put("effective_stats", calculator.effectiveStats(statRows));
        value.put("stat_rows", statRows); value.put("stat_warnings", warnings);
        value.put("weapon_slots", Map.copyOf(weaponSlots)); value.put("weapon_capacity", Map.copyOf(weaponCapacity));
        value.put("weapon_total", weaponSlots.values().stream().mapToLong(Long::longValue).sum());
        value.put("weapon_capacity_total", weaponCapacity.values().stream().mapToLong(Long::longValue).sum());
        value.put("special_crew_total", countRows(slots, "special_crew"));
        value.put("inventory_slots_used", ammunition + consumables + hold);
        value.put("ammunition_slots_used", ammunition); value.put("consumable_slots_used", consumables);
        value.put("hold_slots_used", hold);
        return BuildDtoMapper.shipStats(value, contracts);
    }

    private static long effectiveCrewCapacity(BuildShipSnapshot ship, BuildEffects effects) {
        double multiplier = 1;
        for (Map<String, Number> set : effects.sets()) multiplier *= 1 + decimal(set.get("crew_capacity_pct")) / 100;
        return Math.max(0, BuildStatCalculator.roundWhole(
                ship.crewCapacity() * multiplier + decimal(effects.totals().get("crew_capacity"))));
    }

    private Map<String, Number> specialistEffects(BuildPayload payload, BuildShipSnapshot ship,
                                                   BuildFeatureSnapshot feature, List<BuildSlotSelection> slots,
                                                   BuildEffects all) {
        List<BuildSlotSelection> specialists = slots.stream().filter(slot -> slot.type().equals("special_crew")).toList();
        if (specialists.isEmpty()) return Map.of();
        List<BuildSlotSelection> nonSpecialists = slots.stream().filter(slot -> !slot.type().equals("special_crew")).toList();
        Map<String, Number> without = effects.resolve(payload, ship, feature, nonSpecialists).totals();
        Map<String, Number> result = new LinkedHashMap<>();
        all.totals().forEach((key, value) -> {
            double difference = value.doubleValue() - decimal(without.get(key));
            if (difference != 0) result.put(key, normalized(difference));
        });
        return Map.copyOf(result);
    }

    private static Map<String, Number> effectsFor(List<BuildSlotSelection> slots, String type) {
        Map<String, Number> result = new LinkedHashMap<>();
        slots.stream().filter(slot -> slot.type().equals(type)).forEach(slot -> slot.option().effects().forEach(
                (key, value) -> result.merge(key, value, BuildStatsService::sum)));
        return Map.copyOf(result);
    }

    private static List<String> warnings(BuildPayload payload, long capacity, long minimum, UpgradeSlotAccess access) {
        List<String> warnings = new ArrayList<>();
        long crew = payload.sailors() + payload.soldiers() + payload.musketeers() + payload.mercenaries();
        if (crew > capacity) warnings.add("Crew exceeds effective capacity after upgrade modifiers.");
        if (payload.sailors() < minimum) warnings.add("Sailor count is below the required minimum.");
        for (int index = 5; index <= 8; index++) {
            if (payload.upgrades().get(index - 1) != null && index > access.availableSlots()) {
                warnings.add("Upgrade slot " + index + " is selected without enough upgrade-slot capacity.");
            }
        }
        return List.copyOf(warnings);
    }

    private static long countRows(List<BuildSlotSelection> slots, String type) {
        return slots.stream().filter(slot -> slot.type().equals(type)).count();
    }
    private static int integer(Number value) { return value == null ? 0 : value.intValue(); }
    private static double decimal(Number value) { return value == null ? 0 : value.doubleValue(); }
    private static Number normalized(double value) { return value == Math.rint(value) ? (long) value : value; }
    private static Number sum(Number left, Number right) { return normalized(left.doubleValue() + right.doubleValue()); }
}
