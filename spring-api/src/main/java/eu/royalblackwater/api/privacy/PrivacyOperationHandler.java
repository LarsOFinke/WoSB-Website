package eu.royalblackwater.api.privacy;

import eu.royalblackwater.api.contract.CookieConsentChoice;
import eu.royalblackwater.api.contract.DataSubjectRequestCreate;
import eu.royalblackwater.api.contract.DataSubjectRequestResolve;
import eu.royalblackwater.api.contract.PrivacyContactResolve;
import eu.royalblackwater.api.contract.PrivacyContactCreate;
import eu.royalblackwater.api.security.AuthenticatedUser;
import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import jakarta.servlet.http.HttpServletRequest;
import java.util.Map;
import java.util.Set;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class PrivacyOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS = Set.of(
            "create_privacy_contact_api_privacy_contact_post",
            "get_cookie_consent_api_privacy_cookie_consent_get",
            "save_cookie_consent_api_privacy_cookie_consent_post",
            "get_cookie_policy_api_privacy_cookie_policy_get",
            "export_personal_data_api_privacy_data_export_get",
            "list_my_data_subject_requests_api_privacy_requests_get",
            "create_data_subject_request_api_privacy_requests_post",
            "list_privacy_requests_api_admin_privacy_requests_get",
            "list_privacy_contacts_api_admin_privacy_requests_contacts_get",
            "resolve_privacy_contact_api_admin_privacy_requests_contacts__request_id__put",
            "resolve_privacy_request_api_admin_privacy_requests__request_id__put");

    private final PrivacyService privacy;
    private final PersonalDataExportService export;
    private final CookieConsentService consent;
    private final PrivacyAdministrationService administration;
    private final HttpServletRequest request;

    public PrivacyOperationHandler(PrivacyService privacy, PersonalDataExportService export,
                                   CookieConsentService consent, PrivacyAdministrationService administration, HttpServletRequest request) {
        this.privacy = privacy;
        this.export = export;
        this.consent = consent;
        this.administration = administration;
        this.request = request;
    }

    @Override
    public Set<String> operations() {
        return OPERATIONS;
    }

    @Override
    protected Object execute(String operationId, Map<String, Object> parameters, Object body, MultipartFile upload) {
        return switch (operationId) {
            case "create_privacy_contact_api_privacy_contact_post" ->
                    privacy.createContact(body(body, PrivacyContactCreate.class), CurrentUser.optional().orElse(null));
            case "get_cookie_consent_api_privacy_cookie_consent_get" -> consent.state(request);
            case "save_cookie_consent_api_privacy_cookie_consent_post" -> saveConsent(body(body, CookieConsentChoice.class));
            case "get_cookie_policy_api_privacy_cookie_policy_get" -> consent.policy();
            case "export_personal_data_api_privacy_data_export_get" -> export.build(CurrentUser.require());
            case "list_my_data_subject_requests_api_privacy_requests_get" ->
                    privacy.listRequests(CurrentUser.require().id());
            case "create_data_subject_request_api_privacy_requests_post" ->
                    privacy.createRequest(CurrentUser.require(), body(body, DataSubjectRequestCreate.class));
            case "list_privacy_requests_api_admin_privacy_requests_get" -> administration.listRequests();
            case "list_privacy_contacts_api_admin_privacy_requests_contacts_get" -> administration.listContacts();
            case "resolve_privacy_contact_api_admin_privacy_requests_contacts__request_id__put" ->
                    administration.resolveContact(longParameter(parameters, "request_id"),
                            body(body, PrivacyContactResolve.class), CurrentUser.require());
            case "resolve_privacy_request_api_admin_privacy_requests__request_id__put" ->
                    administration.resolveRequest(longParameter(parameters, "request_id"),
                            body(body, DataSubjectRequestResolve.class), CurrentUser.require());
            default -> throw new IllegalStateException("Unsupported privacy operation: " + operationId);
        };
    }

    private ResponseEntity<?> saveConsent(CookieConsentChoice choice) {
        AuthenticatedUser user = CurrentUser.optional().orElse(null);
        CookieConsentService.SavedConsent saved = consent.save(choice, request, user);
        return ResponseEntity.ok()
                .header(HttpHeaders.SET_COOKIE, saved.cookie().toString())
                .body(saved.body());
    }
}
