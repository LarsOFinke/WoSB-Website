package eu.royalblackwater.api.privacy.repository.queries;

/** SQL statements owned by the PrivacyAdministrationService persistence boundary. */
public final class PrivacyAdministrationQueries {
    private PrivacyAdministrationQueries() { }

    public static final String LIST_REQUESTS_SELECT_01 = """
                select r.id,r.subject_user_id,u.username subject_username,r.request_type,r.status,
                       r.details,r.resolution_note,r.handled_by_user_id,r.created_at,r.resolved_at
                from data_subject_requests r join users u on u.id=r.subject_user_id
                order by case when r.status='pending' then 0 else 1 end,r.created_at asc,r.id asc
                limit 250
                """;

    public static final String LIST_CONTACTS_SELECT_01 = """
                select id,user_id,reply_email,subject,message,status,resolution_note,handled_by_user_id,
                       created_at,resolved_at
                from privacy_contact_requests
                order by case when status='pending' then 0 else 1 end,created_at asc,id asc
                limit 250
                """;

    public static final String RESOLVE_CONTACT_SELECT_01 = "select * from privacy_contact_requests where id=:id for update";

    public static final String RESOLVE_CONTACT_UPDATE_01 = """
                update privacy_contact_requests set status=:status,resolution_note=:note,
                    handled_by_user_id=:actorId,resolved_at=:resolvedAt where id=:id
                """;

    public static final String RESOLVE_CONTACT_SELECT_02 = "select * from privacy_contact_requests where id=:id";

    public static final String RESOLVE_REQUEST_SELECT_01 = """
                select r.*,u.username subject_username,u.is_bootstrap_admin
                from data_subject_requests r join users u on u.id=r.subject_user_id
                where r.id=:id for update of r,u
                """;

    public static final String RESOLVE_REQUEST_UPDATE_01 = """
                update data_subject_requests set status=:status,resolution_note=:note,
                    handled_by_user_id=:actorId,resolved_at=:resolvedAt where id=:id
                """;

    public static final String RESOLVE_REQUEST_SELECT_02 = """
                select r.id,r.subject_user_id,u.username subject_username,r.request_type,r.status,
                       r.details,r.resolution_note,r.handled_by_user_id,r.created_at,r.resolved_at
                from data_subject_requests r join users u on u.id=r.subject_user_id where r.id=:id
                """;

    public static final String PSEUDONYMIZE_DELETE_01 = "delete from auth_sessions where user_id=:id";

    public static final String PSEUDONYMIZE_DELETE_02 = "delete from fleet_memberships where user_id=:id";

    public static final String PSEUDONYMIZE_DELETE_03 = "delete from group_members where user_id=:id";

    public static final String PSEUDONYMIZE_DELETE_04 = "delete from build_votes where user_id=:id";

    public static final String PSEUDONYMIZE_DELETE_05 = "delete from user_profiles where user_id=:id";

    public static final String PSEUDONYMIZE_UPDATE_01 = """
                update privacy_contact_requests set user_id=null,reply_email='deleted@example.invalid',
                    message='[removed with account deletion]' where user_id=:id
                """;

    public static final String PSEUDONYMIZE_UPDATE_02 = "update audit_logs set actor_username='[deleted user]' where actor_username=:username";

    public static final String PSEUDONYMIZE_UPDATE_03 = """
                update users set username=:username,password_hash=:passwordHash,is_active=false,updated_at=:updatedAt
                where id=:id
                """;

    public static final String NULL_NULLABLE_USER_REFERENCES_SELECT_01 = """
                select tc.table_name,kcu.column_name
                from information_schema.table_constraints tc
                join information_schema.key_column_usage kcu
                  on tc.constraint_schema=kcu.constraint_schema and tc.constraint_name=kcu.constraint_name
                join information_schema.constraint_column_usage ccu
                  on tc.constraint_schema=ccu.constraint_schema and tc.constraint_name=ccu.constraint_name
                join information_schema.columns cols
                  on cols.table_schema=tc.table_schema and cols.table_name=tc.table_name
                 and cols.column_name=kcu.column_name
                where tc.constraint_type='FOREIGN KEY' and tc.table_schema=current_schema()
                  and ccu.table_name='users' and ccu.column_name='id' and cols.is_nullable='YES'
                """;

    public static final String UNIQUE_DELETED_USERNAME_SELECT_01 = "select count(*) from users where username=:username";

}
