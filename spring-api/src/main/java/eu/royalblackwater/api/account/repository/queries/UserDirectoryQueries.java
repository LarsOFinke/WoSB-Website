package eu.royalblackwater.api.account.repository.queries;

/** SQL statements owned by the UserDirectoryService persistence boundary. */
public final class UserDirectoryQueries {
    private UserDirectoryQueries() { }

    public static final String USER_SELECT = """
            select u.id,u.username,u.is_active,u.is_bootstrap_admin,u.created_at,
                   sr.code role,up.display_name,up.external_fleet_name,up.preferred_focus,
                   up.availability,up.timezone,up.discord_handle,up.note,
                   fm.fleet_id,fm.fleet_name,fm.membership_id,fm.membership_status,fm.membership_role
            from users u join site_roles sr on sr.id=u.site_role_id
            left join user_profiles up on up.user_id=u.id
            left join lateral (
                select f.id fleet_id,f.name fleet_name,m.id membership_id,m.status membership_status,
                       fr.code membership_role
                from fleet_memberships m join fleets f on f.id=m.fleet_id
                join fleet_roles fr on fr.id=m.fleet_role_id
                where m.user_id=u.id and m.status in ('active','pending')
                order by case when m.status='active' then 0 else 1 end,fr.rank desc,m.id asc limit 1
            ) fm on true
            """;

    public static final String LIST_WHERE_01 = " where 1=1";

    public static final String LIST_AND_01 = " and (lower(u.username) like :search or lower(coalesce(up.display_name,'')) like :search";

    public static final String LIST_OR_01 = " or lower(coalesce(fm.fleet_name,'')) like :search)";

    public static final String LIST_AND_02 = " and sr.code=:role";

    public static final String LIST_AND_03 = " and u.is_active=true";

    public static final String LIST_AND_04 = " and u.is_active=false";

    public static final String LIST_AND_05 = " and fm.fleet_id=:fleetId";

    public static final String LIST_ORDER_BY_01 = " order by u.created_at desc,u.id desc limit :limit offset :offset";

    public static final String READ_WHERE_01 = " where u.id=:id";

    public static final String READ_MANY_WHERE_01 = " where u.id in (:ids)";

    public static final String PREFERENCES_SELECT_01 = "select user_id,";

    public static final String PREFERENCES_WHERE_01 = " where user_id in (:ids) order by user_id,sort_order,id";

}
