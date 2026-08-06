package eu.royalblackwater.api.audit.repository.queries;

/** SQL statements owned by the AuditLogQueryService persistence boundary. */
public final class AuditLogQueryQueries {
    private AuditLogQueryQueries() { }

    public static final String LIST_SQL_01 = "limit must be between 1 and 500.";

    public static final String LIST_SELECT_01 = "select * from audit_logs where 1=1";

    public static final String LIST_AND_01 = " and actor_username ilike :actor";

    public static final String LIST_AND_02 = " and created_at>=:fromDate";

    public static final String LIST_AND_03 = " and created_at<:toDate";

    public static final String LIST_ORDER_BY_01 = " order by created_at desc,id desc limit :limit";

}
