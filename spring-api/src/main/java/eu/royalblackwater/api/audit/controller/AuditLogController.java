package eu.royalblackwater.api.audit.controller;

import eu.royalblackwater.api.dto.AuditLogRead;
import java.util.List;
import eu.royalblackwater.api.audit.service.AuditLogQueryService;
import eu.royalblackwater.api.contract.api.AdminAuditLogsApi;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import java.time.LocalDate;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class AuditLogController extends ApiControllerSupport implements AdminAuditLogsApi {

    private final AuditLogQueryService auditLogs;

    public AuditLogController(AuditLogQueryService auditLogs) {
        this.auditLogs = auditLogs;
    }

    @Override
    public ResponseEntity<List<AuditLogRead>> adminAuditLogs(
            String entityType,
            String action,
            String actor,
            LocalDate fromDate,
            LocalDate toDate,
            long limit
    ) {

        return respond(auditLogs.list(entityType,action,
                        actor,fromDate,toDate,
                        limit), 200);
    }
}
