package eu.royalblackwater.api.account.controller;

import eu.royalblackwater.api.dto.RegistrationRequestRead;
import java.util.List;
import eu.royalblackwater.api.account.service.RegistrationAdministrationService;
import eu.royalblackwater.api.dto.RegistrationDecision;
import eu.royalblackwater.api.contract.api.AdminRegistrationRequestsApi;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import java.time.LocalDate;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class RegistrationAdministrationController extends ApiControllerSupport implements AdminRegistrationRequestsApi {

    private final RegistrationAdministrationService registrations;

    public RegistrationAdministrationController(RegistrationAdministrationService registrations) {
        this.registrations = registrations;
    }

    @Override
    public ResponseEntity<List<RegistrationRequestRead>> adminListRegistrationRequests(
            String status,
            String search,
            LocalDate fromDate,
            LocalDate toDate
    ) {

        return respond(registrations.list(
                            status,search,
                            fromDate,toDate), 200);
    }

    @Override
    public ResponseEntity<RegistrationRequestRead> adminApproveRegistrationRequest(
            long requestId,
            RegistrationDecision body
    ) {

        return respond(registrations.approve(requestId,body(body,RegistrationDecision.class),
                                    CurrentUser.require()), 200);
    }

    @Override
    public ResponseEntity<RegistrationRequestRead> adminRejectRegistrationRequest(
            long requestId,
            RegistrationDecision body
    ) {

        return respond(registrations.reject(requestId,body(body,RegistrationDecision.class),
                                    CurrentUser.require()), 200);
    }

    private static LocalDate date(Map<String, Object> parameters, String name) {
        Object value = parameters.get(name);
        return value instanceof LocalDate date ? date : null;
    }
}
