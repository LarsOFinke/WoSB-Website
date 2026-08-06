package eu.royalblackwater.api.fleet.repository.queries;

/** SQL statements owned by the FleetViewService persistence boundary. */
public final class FleetViewQueries {
    private FleetViewQueries() { }

    public static final String FLEET_SELECT = """
            select f.*,
                   (select count(*) from fleet_memberships m where m.fleet_id=f.id and m.status='active') active_count,
                   (select count(*) from fleet_memberships m where m.fleet_id=f.id and m.status='pending') pending_count
            from fleets f
            """;

    public static final String MEMBERSHIP_SELECT = """
            select m.*, r.code as role, r.label as role_label, r.rank as role_rank,
                   f.name as fleet_name, f.slug as fleet_slug, f.focus as fleet_focus, f.is_active as fleet_active,
                   u.username, sr.code as site_role, coalesce(up.display_name, u.username) as display_name,
                   up.availability, up.timezone, up.discord_handle,
                   (select string_agg(s.name, ', ' order by p.sort_order, p.id)
                      from user_profile_ship_preferences p join ships s on s.id=p.ship_id
                     where p.user_id=u.id) as preferred_ships,
                   (select string_agg(fr.label, ', ' order by p.sort_order, p.id)
                      from user_profile_role_preferences p join fleet_roles fr on fr.id=p.fleet_role_id
                     where p.user_id=u.id) as preferred_roles
            from fleet_memberships m
            join fleet_roles r on r.id=m.fleet_role_id
            join fleets f on f.id=m.fleet_id
            join users u on u.id=m.user_id
            join site_roles sr on sr.id=u.site_role_id
            left join user_profiles up on up.user_id=u.id
            """;

    public static final String MEMBERSHIPS_FOR_WHERE_01 = """
                where m.user_id=:userId
                order by m.status asc, m.joined_at desc
                """;

    public static final String MEMBERSHIP_WHERE_01 = " where m.id=:id";

    public static final String OFFICIAL_WHERE_01 = " where f.is_active=true";

    public static final String OFFICIAL_ORDER_BY_01 = " order by case when f.slug='royal-blackwater-fleet' then 0 else 1 end, f.sort_order, f.id limit 1";

    public static final String FLEET_AND_01 = " and f.is_active=true";

    public static final String FLEET_WHERE_01 = " where f.id=:id";

    public static final String MEMBERSHIP_ROWS_AND_01 = " and r.is_leadership=true and m.status='active'";

    public static final String MEMBERSHIP_ROWS_WHERE_01 = " where m.fleet_id=:fleetId";

    public static final String MEMBERSHIP_ROWS_ORDER_BY_01 = """
                order by case when m.status='pending' then 0 when m.status='active' then 1 else 2 end,
                         r.rank desc, lower(coalesce(up.display_name,u.username)), m.id
                """;

}
