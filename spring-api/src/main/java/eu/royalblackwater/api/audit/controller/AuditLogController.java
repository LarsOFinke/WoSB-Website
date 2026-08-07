package eu.royalblackwater.api.audit.controller;

import eu.royalblackwater.api.audit.service.AuditLogQueryService;
import eu.royalblackwater.api.dto.AuditLogRead;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import java.time.LocalDate;
import java.util.List;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class AuditLogController extends ApiControllerSupport {

    private final AuditLogQueryService auditLogs;

    public AuditLogController(AuditLogQueryService auditLogs) {
        this.auditLogs = auditLogs;
    }

    @GetMapping("/api/admin/audit-logs")
    public ResponseEntity<List<AuditLogRead>> adminAuditLogs(
            @RequestParam(name = "entity_type", required = false) String entityType,
            @RequestParam(name = "action", required = false) String action,
            @RequestParam(name = "actor", required = false) String actor,
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) @RequestParam(name = "from_date", required = false) LocalDate fromDate,
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) @RequestParam(name = "to_date", required = false) LocalDate toDate,
            @RequestParam(name = "limit", defaultValue = "200") long limit
    ) {

        return respond(auditLogs.list(entityType,action,
                        actor,fromDate,toDate,
                        limit), 200);
    }
}
