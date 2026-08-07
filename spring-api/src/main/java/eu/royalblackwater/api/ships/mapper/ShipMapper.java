package eu.royalblackwater.api.ships.mapper;

import eu.royalblackwater.api.dto.ShipMortarModificationRead;
import eu.royalblackwater.api.dto.ShipRead;
import java.util.Map;
import org.springframework.stereotype.Component;

import static eu.royalblackwater.api.persistence.RowValues.booleanValue;
import static eu.royalblackwater.api.persistence.RowValues.longValue;
import static eu.royalblackwater.api.persistence.RowValues.nullableLong;
import static eu.royalblackwater.api.persistence.RowValues.requiredString;
import static eu.royalblackwater.api.persistence.RowValues.string;

@Component
public class ShipMapper {
    public ShipRead toRead(Map<String, Object> row) {
        long frontSpecial = number(row, "front_special_weapon_capacity").longValue();
        long rearSpecial = number(row, "rear_special_weapon_capacity").longValue();
        long dedicatedSpecial = number(row, "dedicated_special_weapon_capacity").longValue();
        return new ShipRead(
                number(row, "armor").doubleValue(),
                nullableLong(row, "broadside_weapon_capacity"),
                longValue(row, "crew_capacity"),
                nullableLong(row, "dedicated_special_weapon_capacity"),
                longValue(row, "displacement_tons"),
                longValue(row, "durability"),
                nullableLong(row, "front_special_weapon_capacity"),
                nullableLong(row, "front_weapon_capacity"),
                booleanValue(row, "has_lantern"),
                longValue(row, "hold_capacity"),
                longValue(row, "id"),
                string(row, "image_url"),
                booleanValue(row, "is_active"),
                number(row, "maneuverability").doubleValue(),
                nullableNumber(row, "max_mortar_caliber_inches"),
                mortarModification(row),
                nullableLong(row, "mortar_weapon_capacity"),
                requiredString(row, "name"),
                longValue(row, "rate"),
                nullableLong(row, "rear_special_weapon_capacity"),
                nullableLong(row, "rear_weapon_capacity"),
                longValue(row, "sail_slots"),
                longValue(row, "sailor_minimum"),
                requiredString(row, "ship_type"),
                string(row, "source"),
                frontSpecial + rearSpecial + dedicatedSpecial,
                number(row, "speed_knots").doubleValue(),
                number(row, "speed_min_knots").doubleValue(),
                longValue(row, "upgrade_slots"),
                layout(row));
    }

    private static ShipMortarModificationRead mortarModification(Map<String, Object> row) {
        if (row.get("mortar_modification_mortar_capacity") == null) return null;
        return new ShipMortarModificationRead(
                number(row, "mortar_modification_broadside_capacity_delta").longValue(),
                number(row, "mortar_modification_crew_capacity_delta").longValue(),
                number(row, "mortar_modification_durability_delta").longValue(),
                number(row, "mortar_modification_hold_capacity_pct").doubleValue(),
                number(row, "mortar_modification_maneuverability_delta").doubleValue(),
                number(row, "mortar_modification_max_caliber_inches").doubleValue(),
                number(row, "mortar_modification_mortar_capacity").longValue(),
                requiredString(row, "mortar_modification_source"),
                number(row, "mortar_modification_speed_pct").doubleValue());
    }

    private static String layout(Map<String, Object> row) {
        String regular = number(row, "rear_weapon_capacity").longValue() + "-"
                + number(row, "broadside_weapon_capacity").longValue() + "-"
                + number(row, "front_weapon_capacity").longValue();
        java.util.ArrayList<String> suffixes = new java.util.ArrayList<>();
        long mortar = number(row, "mortar_weapon_capacity").longValue();
        if (mortar > 0) suffixes.add("mortar " + number(row, "max_mortar_caliber_inches") + "in x" + mortar);
        long front = number(row, "front_special_weapon_capacity").longValue();
        if (front > 0) suffixes.add("bow special x" + front);
        long rear = number(row, "rear_special_weapon_capacity").longValue();
        if (rear > 0) suffixes.add("stern special x" + rear);
        long dedicated = number(row, "dedicated_special_weapon_capacity").longValue();
        if (dedicated > 0) suffixes.add("special x" + dedicated);
        return suffixes.isEmpty() ? regular : regular + "; " + String.join("; ", suffixes);
    }

    private static Number number(Map<String, Object> row, String key) {
        Number value = nullableNumber(row, key);
        return value == null ? 0L : value;
    }

    private static Number nullableNumber(Map<String, Object> row, String key) {
        Object value = row.get(key);
        return value instanceof Number number ? number : null;
    }
}
