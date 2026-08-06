package eu.royalblackwater.api.groups.repository.queries;

/** SQL statements owned by the GroupService persistence boundary. */
public final class GroupQueries {
    private GroupQueries() { }

    public static final String GROUP_SELECT = """
            select g.*, u.username as owner_username, coalesce(up.display_name,u.username) as owner_display_name,
                   (select count(*) from group_members m where m.group_id=g.id and m.is_active=true) active_count
            from groups g join users u on u.id=g.owner_id left join user_profiles up on up.user_id=u.id
            """;

    public static final String LIST_WHERE_01 = " where 1=1";

    public static final String LIST_AND_01 = " and g.status='open'";

    public static final String LIST_AND_02 = " and g.owner_id=:ownerId";

    public static final String LIST_AND_03 = " and lower(concat_ws(' ',g.title,g.focus,g.description,g.expectations,g.activity_plan,g.contact_note,g.fleet_restriction)) like :search";

    public static final String LIST_AND_04 = " and g.focus=:focus";

    public static final String LIST_AND_05 = " and coalesce(g.max_ship_rate,1)<=:minRate";

    public static final String LIST_AND_06 = " and coalesce(g.min_ship_rate,7)>=:maxRate";

    public static final String LIST_ORDER_BY_01 = " order by g.status asc,g.expires_at asc,g.created_at desc";

    public static final String LIST_ORDER_BY_02 = " order by g.created_at desc,g.id desc";

    public static final String CREATE_INSERT_01 = """
                insert into groups
                    (title, focus, description, expectations, activity_plan, contact_note,
                     scheduled_start_at, scheduled_end_at, max_members, min_ship_rate, max_ship_rate,
                     allow_guests, fleet_restriction, status, owner_id, created_at, updated_at, expires_at)
                values (:title,:focus,:description,:expectations,:activityPlan,:contactNote,
                        :startAt,:endAt,:maxMembers,:minRate,:maxRate,:allowGuests,:fleetRestriction,
                        'open',:ownerId,:now,:now,:expiresAt) returning id
                """;

    public static final String JOIN_SELECT_01 = """
                select count(*) from group_members where group_id=:groupId and user_id=:userId and is_active=true
                """;

    public static final String JOIN_SELECT_02 = """
                    select coalesce(p.display_name,u.username) display_name from users u
                    left join user_profiles p on p.user_id=u.id where u.id=:id
                    """;

    public static final String JOIN_INSERT_01 = """
                insert into group_members
                    (group_id,user_id,is_guest,display_name,fleet_name,ship_id,build_id,ship_name,
                     ship_rate,note,is_active,joined_at)
                values (:groupId,:userId,false,:displayName,:fleetName,:shipId,:buildId,:shipName,
                        :shipRate,:note,true,:now) returning id
                """;

    public static final String JOIN_UPDATE_01 = "update groups set status='full',updated_at=:now where id=:id";

    public static final String JOIN_JOIN_01 = "join";

    public static final String CLOSE_UPDATE_01 = "update groups set status='closed',closed_at=:now,updated_at=:now where id=:id";

    public static final String READ_SELECT_01 = """
                select * from group_members where group_id=:id order by joined_at,id
                """;

    public static final String RESOLVE_SELECTION_SELECT_01 = """
                    select b.id build_id,b.ship_id,s.name ship_name,s.rate ship_rate
                    from builds b join ships s on s.id=b.ship_id
                    where b.id=:buildId and b.owner_id=:ownerId
                    """;

    public static final String RESOLVE_SELECTION_SELECT_02 = """
                    select id,name,rate from ships where id=:id and is_active=true
                    """;

    public static final String RAW_WHERE_01 = " where g.id=:id";

}
