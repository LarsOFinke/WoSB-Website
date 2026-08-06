package eu.royalblackwater.api.calendar.repository.queries;

/** SQL statements owned by the CalendarService persistence boundary. */
public final class CalendarQueries {
    private CalendarQueries() { }

    public static final String EVENT_SELECT = """
            select e.*,s.name squad_name,s.slug squad_slug,s.fleet_id,
                   coalesce(nullif(up.display_name,''),u.username) owner_display_name
            from fleet_events e join users u on u.id=e.owner_id
            left join user_profiles up on up.user_id=u.id
            left join squads s on s.id=e.squad_id
            """;

    public static final String LIST_WHERE_01 = " where e.is_cancelled=false";

    public static final String LIST_AND_01 = """
                     and (e.squad_id is null or exists(
                       select 1 from squad_members sm join fleet_memberships fm on fm.id=sm.fleet_membership_id
                       where sm.squad_id=e.squad_id and fm.user_id=:userId and fm.status='active'))
                    """;

    public static final String LIST_AND_02 = " and e.end_at>=:start";

    public static final String LIST_AND_03 = " and e.start_at<=:end";

    public static final String LIST_AND_04 = " and e.category=:category";

    public static final String LIST_AND_05 = " and e.squad_id is null";

    public static final String LIST_AND_06 = " and e.squad_id=:squadId";

    public static final String LIST_ORDER_BY_01 = " order by e.start_at,e.id limit ";

    public static final String CREATE_INSERT_01 = """
                insert into fleet_events
                  (title,category,description,location,start_at,end_at,all_day,owner_id,squad_id,
                   is_cancelled,raid_helper_enabled,created_at,updated_at)
                values (:title,:category,:description,:location,:startAt,:endAt,:allDay,:ownerId,:squadId,
                        false,:raidHelperEnabled,:now,:now) returning id
                """;

    public static final String UPDATE_UPDATE_01 = """
                update fleet_events set title=:title,category=:category,description=:description,location=:location,
                  start_at=:startAt,end_at=:endAt,all_day=:allDay,squad_id=:squadId,
                  raid_helper_enabled=:raidHelperEnabled,updated_at=:now where id=:id
                """;

    public static final String CANCEL_UPDATE_01 = "update fleet_events set is_cancelled=true,updated_at=:now where id=:id";

    public static final String ROW_WHERE_01 = " where e.id=:id";

    public static final String CAN_VIEW_SQUAD_SELECT_01 = """
                select count(*) from squad_members sm join fleet_memberships fm on fm.id=sm.fleet_membership_id
                where sm.squad_id=:squadId and fm.user_id=:userId and fm.status='active'
                """;

    public static final String MANAGED_SQUAD_IDS_SELECT_01 = """
                select sm.squad_id from squad_members sm
                join fleet_memberships fm on fm.id=sm.fleet_membership_id
                join squad_roles sr on sr.id=sm.squad_role_id
                join squads s on s.id=sm.squad_id
                where fm.user_id=:userId and fm.status='active' and s.fleet_id=:fleetId
                  and s.is_active=true and sr.code in ('leader','officer')
                """;

    public static final String VALIDATE_SCOPE_SELECT_01 = "select fleet_id,is_active from squads where id=:id";

}
