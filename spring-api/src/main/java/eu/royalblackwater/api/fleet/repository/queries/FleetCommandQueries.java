package eu.royalblackwater.api.fleet.repository.queries;

/** SQL statements owned by the FleetCommandService persistence boundary. */
public final class FleetCommandQueries {
    private FleetCommandQueries() { }

    public static final String CREATE_SELECT_01 = "select count(*) from fleets";

    public static final String CREATE_INSERT_01 = """
                insert into fleets
                    (name, slug, focus, description, standing_orders, sort_order, is_active, created_at, updated_at)
                values (:name, :slug, :focus, :description, :standingOrders, :sortOrder, :active, :now, :now)
                returning id
                """;

    public static final String UPDATE_SELECT_01 = "select * from fleets where id=:id";

    public static final String JOIN_SELECT_01 = "select id, status from fleet_memberships where user_id=:userId";

    public static final String JOIN_INSERT_01 = """
                    insert into fleet_memberships
                        (fleet_id, user_id, fleet_role_id, status, note, joined_at, updated_at)
                    values (:fleetId, :userId, :roleId, 'pending', :note, :now, :now)
                    returning id
                    """;

    public static final String JOIN_UPDATE_01 = """
                    update fleet_memberships set fleet_id=:fleetId, status=:status, note=:note, updated_at=:now
                    where id=:id
                    """;

    public static final String ASSIGN_LEADER_SELECT_01 = "select count(*) from users where id=:id";

    public static final String ASSIGN_LEADER_SELECT_02 = "select id from fleet_memberships where user_id=:userId";

    public static final String ASSIGN_LEADER_INSERT_01 = """
                    insert into fleet_memberships
                        (fleet_id, user_id, fleet_role_id, status, joined_at, updated_at)
                    values (:fleetId, :userId, :roleId, 'active', :now, :now) returning id
                    """;

    public static final String ASSIGN_LEADER_UPDATE_01 = """
                    update fleet_memberships
                    set fleet_id=:fleetId, fleet_role_id=:roleId, status='active', updated_at=:now
                    where id=:id
                    """;

    public static final String OFFICIAL_SELECT_01 = """
                select * from fleets where is_active=true
                order by case when slug='royal-blackwater-fleet' then 0 else 1 end, sort_order, id limit 1
                """;

    public static final String TARGET_MEMBERSHIP_SELECT_01 = """
                select m.*, r.code as role, r.rank as role_rank, sr.code as site_role
                from fleet_memberships m join fleet_roles r on r.id=m.fleet_role_id
                join users u on u.id=m.user_id join site_roles sr on sr.id=u.site_role_id
                where m.id=:membershipId and m.fleet_id=:fleetId
                """;

    public static final String ROLE_ID_SELECT_01 = "select id from fleet_roles where code=:code and is_active=true";

    public static final String ENSURE_UNIQUE_AND_01 = " and id<>:id";

    public static final String ENSURE_UNIQUE_SELECT_01 = """
                select count(*) from fleets
                where (lower(name)=lower(:name) or slug=:slug)
                """;

}
