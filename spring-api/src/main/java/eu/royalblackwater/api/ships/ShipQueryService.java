package eu.royalblackwater.api.ships;

import eu.royalblackwater.api.contract.ShipRead;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.RowValues;
import eu.royalblackwater.api.transport.ContractConversionService;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ShipQueryService {
    private static final String SHIP_QUERY = """
            select s.id, s.name, s.rate, s.ship_type, s.durability, s.speed_min_knots, s.speed_knots,
                   s.maneuverability, s.armor, s.hold_capacity, s.crew_capacity, s.sailor_minimum,
                   s.displacement_tons, s.source, s.image_url, s.sail_slots, s.upgrade_slots,
                   s.has_lantern, s.is_active,
                   coalesce(w.front_weapon_capacity, 0) as front_weapon_capacity,
                   greatest(coalesce(w.port_weapon_capacity, 0), coalesce(w.starboard_weapon_capacity, 0))
                       as broadside_weapon_capacity,
                   coalesce(w.rear_weapon_capacity, 0) as rear_weapon_capacity,
                   coalesce(w.mortar_weapon_capacity, 0) as mortar_weapon_capacity,
                   coalesce(w.front_special_weapon_capacity, 0) as front_special_weapon_capacity,
                   coalesce(w.rear_special_weapon_capacity, 0) as rear_special_weapon_capacity,
                   coalesce(w.dedicated_special_weapon_capacity, 0) as dedicated_special_weapon_capacity,
                   w.max_mortar_caliber_inches,
                   mm.mortar_capacity as mortar_modification_mortar_capacity,
                   mm.max_caliber_inches as mortar_modification_max_caliber_inches,
                   mm.broadside_capacity_delta as mortar_modification_broadside_capacity_delta,
                   mm.durability_delta as mortar_modification_durability_delta,
                   mm.speed_pct as mortar_modification_speed_pct,
                   mm.maneuverability_delta as mortar_modification_maneuverability_delta,
                   mm.hold_capacity_pct as mortar_modification_hold_capacity_pct,
                   mm.crew_capacity_delta as mortar_modification_crew_capacity_delta,
                   mm.source as mortar_modification_source
              from ships s
              left join (
                  select m.ship_id,
                         max(m.capacity) filter(where t.code='weapon_front') front_weapon_capacity,
                         max(m.capacity) filter(where t.code='weapon_port') port_weapon_capacity,
                         max(m.capacity) filter(where t.code='weapon_starboard') starboard_weapon_capacity,
                         max(m.capacity) filter(where t.code='weapon_rear') rear_weapon_capacity,
                         max(m.capacity) filter(where t.code='weapon_mortar') mortar_weapon_capacity,
                         max(m.special_weapon_capacity) filter(where t.code='weapon_front') front_special_weapon_capacity,
                         max(m.special_weapon_capacity) filter(where t.code='weapon_rear') rear_special_weapon_capacity,
                         max(m.special_weapon_capacity) filter(where t.code='weapon_special') dedicated_special_weapon_capacity,
                         max(m.max_caliber_inches) filter(where t.code='weapon_mortar') max_mortar_caliber_inches
                    from ship_weapon_mounts m join weapon_slot_types t on t.id=m.slot_type_id
                   group by m.ship_id
              ) w on w.ship_id=s.id
              left join ship_mortar_modifications mm on mm.ship_id=s.id
            """;

    private final JdbcQueryService jdbc;
    private final ContractConversionService contracts;

    public ShipQueryService(JdbcQueryService jdbc, ContractConversionService contracts) {
        this.jdbc = jdbc;
        this.contracts = contracts;
    }

    @Transactional(readOnly = true)
    public List<ShipRead> activeShips(ShipListFilter filter) {
        StringBuilder sql = new StringBuilder(SHIP_QUERY).append(" where s.is_active=true");
        Map<String, Object> parameters = new LinkedHashMap<>();
        if (filter.page().search() != null) {
            sql.append(" and (lower(s.name) like :search or lower(coalesce(s.source,'')) like :search)");
            parameters.put("search", "%" + filter.page().search().toLowerCase(Locale.ROOT) + "%");
        }
        if (filter.rate() != null) {
            sql.append(" and s.rate=:rate");
            parameters.put("rate", filter.rate());
        }
        if (filter.shipType() != null) {
            sql.append(" and lower(s.ship_type)=:shipType");
            parameters.put("shipType", filter.shipType().toLowerCase(Locale.ROOT));
        }
        sql.append(" order by s.rate,s.name,s.id limit :limit offset :offset");
        parameters.put("limit", filter.page().limit());
        parameters.put("offset", filter.page().offset());
        return jdbc.query(sql.toString(), parameters).stream().map(this::toRead).toList();
    }

    @Transactional(readOnly = true)
    public ShipRead activeShip(long shipId) {
        return jdbc.optional(SHIP_QUERY + " where s.is_active=true and s.id=:id", Map.of("id", shipId))
                .map(this::toRead).orElse(null);
    }

    private ShipRead toRead(Map<String, Object> source) {
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
