package eu.royalblackwater.api.account.controller;

import eu.royalblackwater.api.account.service.RegistrationAdministrationService;
import eu.royalblackwater.api.dto.RegistrationDecision;
import eu.royalblackwater.api.dto.RegistrationRequestRead;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import jakarta.validation.Valid;
import java.time.LocalDate;
import java.util.List;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class RegistrationAdministrationController extends ApiControllerSupport {

    private final RegistrationAdministrationService registrations;

    public RegistrationAdministrationController(RegistrationAdministrationService registrations) {
        this.registrations = registrations;
    }

    @GetMapping("/api/admin/registration-requests")
    public ResponseEntity<List<RegistrationRequestRead>> adminListRegistrationRequests(
            @RequestParam(name = "status", defaultValue = "pending") String status,
            @RequestParam(name = "search", required = false) String search,
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) @RequestParam(name = "from_date", required = false) LocalDate fromDate,
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) @RequestParam(name = "to_date", required = false) LocalDate toDate
    ) {

        return respond(registrations.list(
                            status,search,
                            fromDate,toDate), 200);
    }

    @PostMapping("/api/admin/registration-requests/{request_id}/approve")
    public ResponseEntity<RegistrationRequestRead> adminApproveRegistrationRequest(
            @PathVariable("request_id") long requestId,
            @Valid @RequestBody RegistrationDecision body
    ) {

        return respond(registrations.approve(requestId,body,
                                    CurrentUser.require()), 200);
    }

    @PostMapping("/api/admin/registration-requests/{request_id}/reject")
    public ResponseEntity<RegistrationRequestRead> adminRejectRegistrationRequest(
            @PathVariable("request_id") long requestId,
            @Valid @RequestBody RegistrationDecision body
    ) {

        return respond(registrations.reject(requestId,body,
                                    CurrentUser.require()), 200);
    }
}
