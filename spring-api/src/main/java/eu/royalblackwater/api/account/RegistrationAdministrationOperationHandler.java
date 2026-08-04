package eu.royalblackwater.api.account;

import eu.royalblackwater.api.contract.RegistrationDecision;
import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import java.time.LocalDate;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class RegistrationAdministrationOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS = Set.of(
            "admin_list_registration_requests_api_admin_registration_requests_get",
            "admin_approve_registration_request_api_admin_registration_requests__request_id__approve_post",
            "admin_reject_registration_request_api_admin_registration_requests__request_id__reject_post");
    private final RegistrationAdministrationService registrations;

    public RegistrationAdministrationOperationHandler(RegistrationAdministrationService registrations) {
        this.registrations = registrations;
    }

    @Override
    public Set<String> operations() { return OPERATIONS; }

    @Override
    protected Object execute(String operationId, Map<String, Object> parameters, Object body, MultipartFile upload) {
        return switch (operationId) {
            case "admin_list_registration_requests_api_admin_registration_requests_get" -> registrations.list(
                    stringParameter(parameters,"status"),stringParameter(parameters,"search"),
                    date(parameters,"from_date"),date(parameters,"to_date"));
            case "admin_approve_registration_request_api_admin_registration_requests__request_id__approve_post" ->
                    registrations.approve(longParameter(parameters,"request_id"),body(body,RegistrationDecision.class),
                            CurrentUser.require());
            case "admin_reject_registration_request_api_admin_registration_requests__request_id__reject_post" ->
                    registrations.reject(longParameter(parameters,"request_id"),body(body,RegistrationDecision.class),
                            CurrentUser.require());
            default -> throw new IllegalStateException("Unsupported registration administration operation: " + operationId);
        };
    }

    private static LocalDate date(Map<String, Object> parameters, String name) {
        Object value = parameters.get(name);
        return value instanceof LocalDate date ? date : null;
    }
}
