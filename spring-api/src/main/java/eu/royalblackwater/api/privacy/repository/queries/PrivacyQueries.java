package eu.royalblackwater.api.privacy.repository.queries;

/** SQL statements owned by the PrivacyService persistence boundary. */
public final class PrivacyQueries {
    private PrivacyQueries() { }

    public static final String CREATE_CONTACT_SELECT_01 = """
                select count(*) from privacy_contact_requests
                where reply_email = :email and created_at >= :cutoff
                """;

    public static final String CREATE_CONTACT_INSERT_01 = """
                insert into privacy_contact_requests
                    (user_id, reply_email, subject, message, status, created_at)
                values (:userId, :email, :subject, :message, 'pending', :createdAt)
                returning id
                """;

    public static final String LIST_REQUESTS_SELECT_01 = """
                select r.id, r.subject_user_id, u.username as subject_username, r.request_type,
                       r.status, r.details, r.resolution_note, r.handled_by_user_id,
                       r.created_at, r.resolved_at
                from data_subject_requests r
                join users u on u.id = r.subject_user_id
                where r.subject_user_id = :userId
                order by r.created_at desc
                limit 100
                """;

    public static final String CREATE_REQUEST_SELECT_01 = """
                select count(*) from data_subject_requests
                where subject_user_id = :userId and request_type = :type and status = 'pending'
                """;

    public static final String CREATE_REQUEST_INSERT_01 = """
                insert into data_subject_requests
                    (subject_user_id, request_type, status, details, created_at)
                values (:userId, :type, 'pending', :details, :createdAt)
                returning id
                """;

    public static final String CREATE_REQUEST_SELECT_02 = """
                select r.id, r.subject_user_id, u.username as subject_username, r.request_type,
                       r.status, r.details, r.resolution_note, r.handled_by_user_id,
                       r.created_at, r.resolved_at
                from data_subject_requests r join users u on u.id = r.subject_user_id
                where r.id = :id
                """;

}
