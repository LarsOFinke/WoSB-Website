package eu.royalblackwater.api.account.repository.queries;

/** SQL statements owned by the BootstrapAdministratorInitializer persistence boundary. */
public final class BootstrapAdministratorQueries {
    private BootstrapAdministratorQueries() { }

    public static final String INITIALIZE_SELECT_01 = """
                select id from users where is_bootstrap_admin=true order by id limit 1
                """;

    public static final String INITIALIZE_INSERT_01 = """
                insert into user_profiles(user_id,display_name,created_at,updated_at)
                values(:userId,:displayName,:now,:now)
                on conflict(user_id) do nothing
                """;

    public static final String CREATE_ADMINISTRATOR_SELECT_01 = "select count(*) from users where username=:username";

    public static final String CREATE_ADMINISTRATOR_INSERT_01 = """
                insert into users(username,password_hash,site_role_id,is_active,is_bootstrap_admin,created_at,updated_at)
                values(:username,:password,(select id from site_roles where code='admin'),true,true,:now,:now)
                returning id
                """;

    public static final String ENSURE_FLEET_LEADERSHIP_INSERT_01 = """
                insert into fleet_memberships
                    (fleet_id,user_id,fleet_role_id,status,joined_at,updated_at)
                values(:fleetId,:userId,:roleId,'active',:now,:now)
                on conflict(user_id) do update set fleet_id=excluded.fleet_id,
                    fleet_role_id=excluded.fleet_role_id,status='active',updated_at=excluded.updated_at
                where fleet_memberships.fleet_id is distinct from excluded.fleet_id
                   or fleet_memberships.fleet_role_id is distinct from excluded.fleet_role_id
                   or fleet_memberships.status is distinct from 'active'
                """;

    public static final String REQUIRED_SEED_ID_SELECT_01 = "select id from ";

    public static final String REQUIRED_SEED_ID_WHERE_01 = " where ";

}
