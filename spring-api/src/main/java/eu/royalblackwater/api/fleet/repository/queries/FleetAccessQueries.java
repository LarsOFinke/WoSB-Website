package eu.royalblackwater.api.fleet.repository.queries;

/** SQL statements owned by the FleetAccessPolicy persistence boundary. */
public final class FleetAccessQueries {
    private FleetAccessQueries() { }

    public static final String REQUIRE_ROLE_MANAGER_SELECT_01 = """
                select count(*)
                from fleet_memberships m join fleet_roles r on r.id = m.fleet_role_id
                where m.fleet_id = :fleetId and m.user_id = :userId and m.status = 'active'
                  and r.code = 'fleet_admiral'
                """;

    public static final String ACTOR_MEMBERSHIP_SELECT_01 = """
                select r.rank, r.can_manage_members
                from fleet_memberships m join fleet_roles r on r.id = m.fleet_role_id
                where m.user_id = :userId and m.fleet_id = :fleetId and m.status = 'active'
                """;

    public static final String ACTIVE_ADMIRALS_SELECT_01 = """
                select count(*) from fleet_memberships m join fleet_roles r on r.id = m.fleet_role_id
                where m.fleet_id = :fleetId and m.status = 'active' and r.code = 'fleet_admiral'
                """;

    public static final String ROLE_RANK_SELECT_01 = "select rank from fleet_roles where code = :code";

    public static final String ASSIGNABLE_ROLES_SELECT_01 = """
                select code from fleet_roles where is_active = true and code <> 'founder' and rank < :rank
                order by rank asc, code asc
                """;

    public static final String ALL_ASSIGNABLE_ROLES_SELECT_01 = """
                select code from fleet_roles where is_active = true and code <> 'founder'
                order by rank asc, code asc
                """;

}
