package eu.royalblackwater.api.audit.repository.queries;

/** SQL statements owned by the AuditService persistence boundary. */
public final class AuditQueries {
    private AuditQueries() { }

    public static final String RECORD_INSERT_01 = """
                insert into audit_logs
                    (created_at, actor_user_id, actor_username, actor_role, entity_type,
                     entity_id, action, summary, changed_fields_json)
                values (:createdAt, :actorId, :username, :role, :entityType,
                        :entityId, :action, :summary, :changedFields)
                """;

}
