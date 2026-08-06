package eu.royalblackwater.api.account.repository.queries;

/** SQL statements owned by the RegistrationAdministrationService persistence boundary. */
public final class RegistrationAdministrationQueries {
    private RegistrationAdministrationQueries() { }

    public static final String LIST_SELECT_01 = "select * from registration_requests where 1=1";

    public static final String LIST_AND_01 = " and status=:status";

    public static final String LIST_AND_02 = " and (username ilike :search or display_name ilike :search or decision_note ilike :search)";

    public static final String LIST_AND_03 = " and created_at>=:fromDate";

    public static final String LIST_AND_04 = " and created_at<:toDate";

    public static final String LIST_ORDER_BY_01 = " order by created_at desc,id desc limit 250";

    public static final String APPROVE_SELECT_01 = "select count(*) from users where username=:username";

    public static final String APPROVE_INSERT_01 = """
                insert into users(username,password_hash,site_role_id,is_active,is_bootstrap_admin,created_at,updated_at)
                values(:username,:passwordHash,:roleId,true,false,:now,:now) returning id
                """;

    public static final String APPROVE_INSERT_02 = """
                insert into user_profiles(user_id,display_name,created_at,updated_at)
                values(:userId,:displayName,:now,:now)
                """;

    public static final String APPROVE_UPDATE_01 = """
                update registration_requests set status='approved',decision_note=:note,reviewed_by_id=:actorId,
                    reviewed_at=:now,created_user_id=:userId,password_hash=:redacted,updated_at=:now where id=:id
                """;

    public static final String REJECT_UPDATE_01 = """
                update registration_requests set status='rejected',decision_note=:note,reviewed_by_id=:actorId,
                    reviewed_at=:now,password_hash=:redacted,updated_at=:now where id=:id
                """;

    public static final String READ_SELECT_01 = "select * from registration_requests where id=:id";

    public static final String PENDING_SELECT_01 = "select * from registration_requests where id=:id for update";

    public static final String CREATE_FLEET_APPLICATION_SELECT_01 = """
                select * from fleets where is_active=true
                order by case when slug='royal-blackwater-fleet' then 0 else 1 end,sort_order,id limit 1
                """;

    public static final String CREATE_FLEET_APPLICATION_SELECT_02 = "select id from fleet_roles where code='member' and is_active=true";

    public static final String CREATE_FLEET_APPLICATION_INSERT_01 = """
                insert into fleet_memberships(fleet_id,user_id,fleet_role_id,status,note,joined_at,updated_at)
                values(:fleetId,:userId,:roleId,'pending',:note,:now,:now)
                """;

    public static final String ROLE_ID_SELECT_01 = "select id from site_roles where code=:code";

}
