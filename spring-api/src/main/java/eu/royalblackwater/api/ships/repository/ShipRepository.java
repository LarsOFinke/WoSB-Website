package eu.royalblackwater.api.ships.repository;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.persistence.JdbcRepositorySupport;
import java.util.Map;
import java.util.Optional;
import org.springframework.stereotype.Repository;

@Repository
public class ShipRepository extends JdbcRepositorySupport {
    public static final String SHIP_QUERY = """
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

    public ShipRepository(JdbcQueryService jdbc) {
        super(jdbc);
    }

    public Optional<Map<String, Object>> findActive(long shipId) {
        return optional(SHIP_QUERY + " where s.is_active=true and s.id=:id", Map.of("id", shipId));
    }
}
