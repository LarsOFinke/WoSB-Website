package eu.royalblackwater.api.builds;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Component;

@Component
class BuildEffectService {
    private static final Map<String, String[]> DYNAMIC_SPECIALIST_EFFECTS = Map.of(
            "sail_deployment_speed_per_sailor_pct", new String[]{"sail_deployment_speed_pct", "sailors"},
            "item_reload_per_sailor_pct", new String[]{"item_reload_pct", "sailors"},
            "ammo_switch_per_sailor_pct", new String[]{"ammo_switch_speed_pct", "sailors"},
            "low_durability_reload_per_sailor_pct", new String[]{"low_durability_reload_pct", "sailors"},
            "boarding_cargo_weight_per_boarder_pct", new String[]{"boarding_cargo_weight_pct", "boarders"},
            "fishing_catch_per_boarder_pct", new String[]{"fishing_catch_pct", "boarders"},
            "fishing_speed_per_sailor_pct", new String[]{"fishing_speed_pct", "sailors"},
            "repair_speed_per_sailor_pct", new String[]{"repair_speed_pct", "sailors"});

    BuildEffects resolve(BuildPayload payload, BuildShipSnapshot ship, BuildFeatureSnapshot feature,
                         List<BuildSlotSelection> slots) {
        List<Map<String, Number>> sets = new ArrayList<>();
        for (BuildSlotSelection slot : slots) {
            if (slot.option().effects().isEmpty()) continue;
            if (slot.type().equals("special_crew")) sets.add(resolveSpecialist(slot.option().effects(), payload));
            else if (!slot.type().startsWith("weapon_")
                    && !List.of("ammunition", "consumable", "hold").contains(slot.type())) {
                sets.add(slot.option().effects());
            }
        }
        if (feature != null && !feature.effects().isEmpty()) sets.add(feature.effects());
        Map<String, Number> mortar = ship.mortarEffects(payload.mortarModification());
        if (!mortar.isEmpty()) sets.add(mortar);
        return new BuildEffects(List.copyOf(sets), aggregate(sets));
    }

    private static Map<String, Number> resolveSpecialist(Map<String, Number> effects, BuildPayload payload) {
        Map<String, Number> resolved = new LinkedHashMap<>();
        long boarders = payload.soldiers() + payload.musketeers() + payload.mercenaries();
        for (Map.Entry<String, Number> entry : effects.entrySet()) {
            String[] dynamic = DYNAMIC_SPECIALIST_EFFECTS.get(entry.getKey());
            if (dynamic != null) {
                long count = "boarders".equals(dynamic[1]) ? boarders : payload.sailors();
                resolved.merge(dynamic[0], entry.getValue().doubleValue() * count, BuildEffectService::sum);
            } else if (entry.getKey().endsWith("_enabled")) {
                resolved.put(entry.getKey(), 1L);
            } else {
                resolved.merge(entry.getKey(), entry.getValue(), BuildEffectService::sum);
            }
        }
        return Map.copyOf(resolved);
    }

    private static Map<String, Number> aggregate(List<Map<String, Number>> sets) {
        Map<String, Number> totals = new LinkedHashMap<>();
        for (Map<String, Number> set : sets) {
            for (Map.Entry<String, Number> entry : set.entrySet()) {
                totals.merge(entry.getKey(), entry.getValue(), BuildEffectService::sum);
            }
        }
        return Map.copyOf(totals);
    }

    private static Number sum(Number left, Number right) {
        double result = left.doubleValue() + right.doubleValue();
        return result == Math.rint(result) ? (long) result : result;
    }
}

record BuildEffects(List<Map<String, Number>> sets, Map<String, Number> totals) { }
