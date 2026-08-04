package eu.royalblackwater.api.audit;

import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import java.time.LocalDate;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class AuditLogOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS = Set.of("admin_audit_logs_api_admin_audit_logs_get");
    private final AuditLogQueryService auditLogs;

    public AuditLogOperationHandler(AuditLogQueryService auditLogs) {
        this.auditLogs = auditLogs;
    }

    @Override
    public Set<String> operations() { return OPERATIONS; }

    @Override
    protected Object execute(String operationId, Map<String, Object> parameters, Object body, MultipartFile upload) {
        return auditLogs.list(stringParameter(parameters,"entity_type"),stringParameter(parameters,"action"),
                stringParameter(parameters,"actor"),date(parameters,"from_date"),date(parameters,"to_date"),
                longParameter(parameters,"limit"));
    }

    private static LocalDate date(Map<String, Object> parameters, String name) {
        return parameters.get(name) instanceof LocalDate value ? value : null;
    }
}
