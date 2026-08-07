package eu.royalblackwater.api.builds.service;

import eu.royalblackwater.api.builds.mapper.BuildDtoMapper;
import eu.royalblackwater.api.builds.dto.BuildEffects;
import eu.royalblackwater.api.builds.dto.BuildFeatureSnapshot;
import eu.royalblackwater.api.builds.dto.BuildStatsSnapshot;
import eu.royalblackwater.api.builds.dto.BuildPayload;
import eu.royalblackwater.api.builds.dto.BuildShipSnapshot;
import eu.royalblackwater.api.builds.dto.BuildSlotSelection;
import eu.royalblackwater.api.builds.dto.UpgradeSlotAccess;
import eu.royalblackwater.api.dto.BuildStatRow;
import eu.royalblackwater.api.dto.ShipStats;
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

    public BuildStatsService(BuildEffectService effects, UpgradeSlotService upgradeSlots,
                      BuildStatCalculator calculator) {
        this.effects = effects;
        this.upgradeSlots = upgradeSlots;
        this.calculator = calculator;
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
        BuildStatsSnapshot snapshot = new BuildStatsSnapshot(
                ammunition,
                (long) ship.crewCapacity(),
                (long) ship.sailorMinimum(),
                (long) ship.sailorMinimum(),
                ship.baseStats(),
                (long) access.baseSlots(),
                consumables,
                crewCapacity,
                Math.max(crewCapacity - crewTotal, 0),
                crewTotal,
                crewCapacity,
                sailorMinimum,
                sailorMinimum,
                calculator.effectiveStats(statRows),
                (long) access.expansionSlots(),
                (long) integer(upgradeEffects.get("extra_upgrade_slots")),
                hold,
                ammunition + consumables + hold,
                resolved.totals(),
                lanternEffects,
                ship.mortarEffects(payload.mortarModification()),
                payload.mortarModification(),
                feature == null ? Map.of() : feature.effects(),
                (long) access.researchSlots(),
                sailEffects,
                sailingEfficiency,
                sailorMinimum,
                sailorMinimum,
                payload.sailors() >= sailorMinimum,
                (long) access.shipExtraSlots(),
                specialistEffects,
                countRows(slots, "special_crew"),
                statRows,
                warnings,
                Map.copyOf(buffs),
                Map.copyOf(debuffs),
                upgradeEffects,
                access.slot5(),
                access.slot6(),
                access.slot6(),
                access.slot7(),
                access.slot8(),
                access.availableSlots(),
                upgradeUsed,
                Map.copyOf(weaponCapacity),
                weaponCapacity.values().stream().mapToLong(Long::longValue).sum(),
                Map.copyOf(weaponSlots),
                weaponSlots.values().stream().mapToLong(Long::longValue).sum());
        return BuildDtoMapper.shipStats(snapshot);
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
