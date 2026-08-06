package eu.royalblackwater.api.squads.repository.queries;

/** SQL statements owned by the SquadService persistence boundary. */
public final class SquadQueries {
    private SquadQueries() { }

    public static final String SQUAD_SELECT = """
            select s.*, (select count(*) from squad_members sm where sm.squad_id=s.id) member_count
            from squads s
            """;

    public static final String MEMBER_SELECT = """
            select sm.*, sr.code as squad_role, fr.code as fleet_role, fm.user_id,
                   coalesce(up.display_name,u.username) as display_name
            from squad_members sm join squad_roles sr on sr.id=sm.squad_role_id
            join fleet_memberships fm on fm.id=sm.fleet_membership_id
            join fleet_roles fr on fr.id=fm.fleet_role_id
            join users u on u.id=fm.user_id left join user_profiles up on up.user_id=u.id
            """;

    public static final String LIST_WHERE_01 = " where 1=1";

    public static final String LIST_AND_01 = " and s.is_active=true";

    public static final String LIST_AND_02 = """
                     and (s.is_active=true or exists(
                         select 1 from fleet_memberships fm join fleet_roles fr on fr.id=fm.fleet_role_id
                         where fm.fleet_id=s.fleet_id and fm.user_id=:accessUserId and fm.status='active'
                           and fr.can_manage_fleet=true and fr.is_active=true))
                    """;

    public static final String LIST_AND_03 = " and exists(select 1 from squad_members sm join fleet_memberships fm";

    public static final String LIST_ON_01 = " on fm.id=sm.fleet_membership_id where sm.squad_id=s.id";

    public static final String LIST_AND_04 = " and fm.user_id=:userId and fm.status='active')";

    public static final String LIST_AND_05 = " and (lower(s.name) like :search or lower(coalesce(s.description,'')) like :search";

    public static final String LIST_OR_01 = " or lower(coalesce(s.focus,'')) like :search)";

    public static final String LIST_AND_06 = " and s.fleet_id=:fleetId";

    public static final String LIST_ORDER_BY_01 = " order by s.name,s.id limit :limit offset :offset";

    public static final String ROSTER_SELECT_01 = """
                select fm.id fleet_membership_id,fm.user_id,fr.code fleet_role,
                       coalesce(up.display_name,u.username) display_name,
                       coalesce(array_agg(sm.squad_id order by sm.squad_id)
                           filter(where s.is_active=true),array[]::integer[]) squad_ids
                from fleet_memberships fm join users u on u.id=fm.user_id
                join fleet_roles fr on fr.id=fm.fleet_role_id
                left join user_profiles up on up.user_id=u.id
                left join squad_members sm on sm.fleet_membership_id=fm.id
                left join squads s on s.id=sm.squad_id
                where fm.fleet_id=:fleetId and fm.status='active'
                group by fm.id,fm.user_id,fr.code,up.display_name,u.username
                order by lower(coalesce(up.display_name,u.username))
                """;

    public static final String CREATE_INSERT_01 = """
                insert into squads(fleet_id,name,slug,description,focus,max_members,is_active,created_by_id,created_at,updated_at)
                values(:fleetId,:name,:slug,:description,:focus,:maxMembers,true,:actorId,:now,:now) returning id
                """;

    public static final String CREATE_INSERT_02 = """
                insert into squad_members(squad_id,fleet_membership_id,squad_role_id,joined_at,updated_at)
                values(:squadId,:membershipId,:roleId,:now,:now) returning id
                """;

    public static final String ARCHIVE_UPDATE_01 = "update squads set is_active=false,updated_at=:now where id=:id";

    public static final String ADD_MEMBER_SELECT_01 = """
                select id from squad_members where squad_id=:squadId and fleet_membership_id=:membershipId
                """;

    public static final String ADD_MEMBER_INSERT_01 = """
                    insert into squad_members(squad_id,fleet_membership_id,squad_role_id,note,joined_at,updated_at)
                    values(:squadId,:membershipId,:roleId,:note,:now,:now) returning id
                    """;

    public static final String ADD_MEMBER_UPDATE_01 = """
                    update squad_members set squad_role_id=:roleId,note=:note,updated_at=:now where id=:id
                    """;

    public static final String REMOVE_MEMBER_DELETE_01 = "delete from squad_members where id=:id";

    public static final String MEMBER_ROWS_WHERE_01 = """
                where sm.squad_id in (:ids)
                order by sm.squad_id,sr.rank desc,lower(coalesce(up.display_name,u.username))
                """;

    public static final String RAW_WHERE_01 = " where s.id=:id";

    public static final String MEMBER_RAW_WHERE_01 = " where sm.squad_id=:squadId and sm.id=:memberId";

    public static final String OFFICIAL_FLEET_SELECT_01 = """
                select * from fleets where is_active=true
                order by case when slug='royal-blackwater-fleet' then 0 else 1 end,sort_order,id limit 1
                """;

    public static final String ACTIVE_MEMBERSHIP_SELECT_01 = """
                select * from fleet_memberships where id=:id and fleet_id=:fleetId and status='active'
                """;

    public static final String ROLE_ID_SELECT_01 = "select id from squad_roles where code=:code";

    public static final String TRANSFER_LEADERSHIP_UPDATE_01 = """
                update squad_members set squad_role_id=case when id=:memberId then :leader else :officer end,
                       updated_at=:now
                where squad_id=:squadId and (id=:memberId or squad_role_id=:leader)
                """;

    public static final String ENSURE_UNIQUE_NAME_AND_01 = " and id<>:excluded";

    public static final String ENSURE_UNIQUE_NAME_SELECT_01 = """
                select count(*) from squads where fleet_id=:fleetId and lower(name)=lower(:name)
                """;

    public static final String UNIQUE_SLUG_SELECT_01 = """
                    select count(*) from squads where fleet_id=:fleetId and slug=:slug
                    """;

}
