package eu.royalblackwater.api.privacy.repository.queries;

/** SQL statements owned by the PrivacyRetentionService persistence boundary. */
public final class PrivacyRetentionQueries {
    private PrivacyRetentionQueries() { }

    public static final String CLEAN_DELETE_01 = """
                delete from cookie_consent_decisions
                where created_at < :cutoff
                """;

    public static final String CLEAN_DELETE_02 = """
                delete from data_subject_requests
                where status in ('completed', 'rejected') and resolved_at < :cutoff
                """;

    public static final String CLEAN_DELETE_03 = """
                delete from privacy_contact_requests
                where status in ('completed', 'rejected') and resolved_at < :cutoff
                """;

}
