package eu.royalblackwater.api.fleet.repository.queries;

/** SQL statements owned by the FleetRoleService persistence boundary. */
public final class FleetRoleQueries {
    private FleetRoleQueries() { }

    public static final String SELECT = """
            select r.*, (select count(*) from fleet_memberships m where m.fleet_role_id=r.id) member_count
            from fleet_roles r
            """;

    public static final String LIST_WHERE_01 = " where r.is_active=true";

    public static final String LIST_ORDER_BY_01 = " order by r.rank desc, r.label asc";

    public static final String CREATE_SELECT_01 = "select count(*) from fleet_roles where code=:code";

    public static final String CREATE_INSERT_01 = """
                insert into fleet_roles
                    (code, label, rank, is_leadership, can_manage_fleet, can_manage_members,
                     is_system, is_active, created_at, updated_at)
                values (:code, :label, :rank, :leadership, :manageFleet, :manageMembers,
                        false, true, :now, :now) returning id
                """;

    public static final String DELETE_DELETE_01 = "delete from fleet_roles where id=:id";

    public static final String RAW_WHERE_01 = " where r.id=:id";

}
