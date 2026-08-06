package eu.royalblackwater.api.account.repository.queries;

/** SQL statements owned by the UserAdministrationService persistence boundary. */
public final class UserAdministrationQueries {
    private UserAdministrationQueries() { }

    public static final String UPDATE_SELECT_01 = "select id from site_roles where code=:code";

    public static final String UPDATE_UPDATE_01 = "update users set site_role_id=:roleId where id=:id";

    public static final String UPDATE_UPDATE_02 = "update users set is_active=:active where id=:id";

    public static final String UPDATE_UPDATE_03 = "update users set updated_at=:now where id=:id";

    public static final String UPDATE_DELETE_01 = "delete from auth_sessions where user_id=:id";

    public static final String CREATE_MODERATOR_SELECT_01 = """
                select (select count(*) from users where username=:username)
                     + (select count(*) from registration_requests where username=:username and status='pending')
                """;

    public static final String CREATE_MODERATOR_SELECT_02 = "select id from site_roles where code='moderator'";

    public static final String CREATE_MODERATOR_INSERT_01 = """
                insert into users(username,password_hash,site_role_id,is_active,is_bootstrap_admin,created_at,updated_at)
                values(:username,:passwordHash,:roleId,true,false,:now,:now) returning id
                """;

    public static final String CREATE_MODERATOR_INSERT_02 = """
                insert into user_profiles(user_id,display_name,created_at,updated_at)
                values(:userId,:displayName,:now,:now)
                """;

    public static final String ACTIVE_ADMIN_COUNT_SELECT_01 = """
                select count(*) from users u join site_roles r on r.id=u.site_role_id
                where r.code='admin' and u.is_active=true
                """;

    public static final String ACCOUNT_SELECT_01 = """
                select u.id,u.username,u.is_active,u.is_bootstrap_admin,r.code role,r.rank role_rank
                from users u join site_roles r on r.id=u.site_role_id where u.id=:id
                """;

}
