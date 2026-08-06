package eu.royalblackwater.api.ships.mapper;

import eu.royalblackwater.api.dto.ShipRead;
import eu.royalblackwater.api.shared.mapper.ContractConversionService;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.stereotype.Component;

@Component
public class ShipMapper {
    private final ContractConversionService contracts;

    public ShipMapper(ContractConversionService contracts) {
        this.contracts = contracts;
    }

    public ShipRead toRead(Map<String, Object> source) {
        Map<String, Object> row = new LinkedHashMap<>(source);
        long frontSpecial = number(row.get("front_special_weapon_capacity"));
        long rearSpecial = number(row.get("rear_special_weapon_capacity"));
        long dedicatedSpecial = number(row.get("dedicated_special_weapon_capacity"));
        row.put("special_weapon_capacity", frontSpecial + rearSpecial + dedicatedSpecial);
        row.put("weapon_layout", layout(row));
        if (row.get("mortar_modification_mortar_capacity") != null) {
            row.put("mortar_modification", nullableMap(
                    "mortar_capacity", row.remove("mortar_modification_mortar_capacity"),
                    "max_caliber_inches", row.remove("mortar_modification_max_caliber_inches"),
                    "broadside_capacity_delta", row.remove("mortar_modification_broadside_capacity_delta"),
                    "durability_delta", row.remove("mortar_modification_durability_delta"),
                    "speed_pct", row.remove("mortar_modification_speed_pct"),
                    "maneuverability_delta", row.remove("mortar_modification_maneuverability_delta"),
                    "hold_capacity_pct", row.remove("mortar_modification_hold_capacity_pct"),
                    "crew_capacity_delta", row.remove("mortar_modification_crew_capacity_delta"),
                    "source", row.remove("mortar_modification_source")));
        } else {
            row.put("mortar_modification", null);
            row.keySet().removeIf(key -> key.startsWith("mortar_modification_"));
        }
        return contracts.convert(row, ShipRead.class);
    }

    private static Map<String, Object> nullableMap(Object... values) {
        Map<String, Object> result = new LinkedHashMap<>();
        for (int index = 0; index < values.length; index += 2) {
            result.put(String.valueOf(values[index]), values[index + 1]);
        }
        return result;
    }

    private static String layout(Map<String, Object> row) {
        String regular = number(row.get("rear_weapon_capacity")) + "-"
                + number(row.get("broadside_weapon_capacity")) + "-"
                + number(row.get("front_weapon_capacity"));
        java.util.ArrayList<String> suffixes = new java.util.ArrayList<>();
        long mortar = number(row.get("mortar_weapon_capacity"));
        if (mortar > 0) suffixes.add("mortar " + number(row.get("max_mortar_caliber_inches")) + "in x" + mortar);
        long front = number(row.get("front_special_weapon_capacity"));
        if (front > 0) suffixes.add("bow special x" + front);
        long rear = number(row.get("rear_special_weapon_capacity"));
        if (rear > 0) suffixes.add("stern special x" + rear);
        long dedicated = number(row.get("dedicated_special_weapon_capacity"));
        if (dedicated > 0) suffixes.add("special x" + dedicated);
        return suffixes.isEmpty() ? regular : regular + "; " + String.join("; ", suffixes);
    }

    private static long number(Object value) {
        return value instanceof Number number ? number.longValue() : 0;
    }
}
