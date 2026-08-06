package eu.royalblackwater.api.ships.repository.queries;

/** SQL statements owned by the ShipQueryService persistence boundary. */
public final class ShipQueryQueries {
    private ShipQueryQueries() { }

    public static final String ACTIVE_SHIPS_WHERE_01 = " where s.is_active=true";

    public static final String ACTIVE_SHIPS_AND_01 = " and (lower(s.name) like :search or lower(coalesce(s.source,'')) like :search)";

    public static final String ACTIVE_SHIPS_AND_02 = " and s.rate=:rate";

    public static final String ACTIVE_SHIPS_AND_03 = " and lower(s.ship_type)=:shipType";

    public static final String ACTIVE_SHIPS_ORDER_BY_01 = " order by s.rate,s.name,s.id limit :limit offset :offset";

}
