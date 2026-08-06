package eu.royalblackwater.api.privacy.controller;

import eu.royalblackwater.api.dto.CookieConsentPolicy;
import eu.royalblackwater.api.dto.CookieConsentRead;
import eu.royalblackwater.api.dto.DataSubjectRequestRead;
import eu.royalblackwater.api.dto.PersonalDataExportRead;
import eu.royalblackwater.api.dto.PrivacyContactRead;
import eu.royalblackwater.api.dto.PrivacyContactReceipt;
import java.util.List;
import eu.royalblackwater.api.dto.CookieConsentChoice;
import eu.royalblackwater.api.dto.DataSubjectRequestCreate;
import eu.royalblackwater.api.dto.DataSubjectRequestResolve;
import eu.royalblackwater.api.dto.PrivacyContactCreate;
import eu.royalblackwater.api.dto.PrivacyContactResolve;
import eu.royalblackwater.api.contract.api.AdminPrivacyRequestsApi;
import eu.royalblackwater.api.contract.api.PrivacyApi;
import eu.royalblackwater.api.privacy.service.CookieConsentService;
import eu.royalblackwater.api.privacy.service.PersonalDataExportService;
import eu.royalblackwater.api.privacy.service.PrivacyAdministrationService;
import eu.royalblackwater.api.privacy.service.PrivacyService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class PrivacyController extends ApiControllerSupport implements AdminPrivacyRequestsApi, PrivacyApi {

    private final PrivacyService privacy;
    private final PersonalDataExportService export;
    private final CookieConsentService consent;
    private final PrivacyAdministrationService administration;
    private final HttpServletRequest request;

    public PrivacyController(PrivacyService privacy, PersonalDataExportService export,
                                   CookieConsentService consent, PrivacyAdministrationService administration, HttpServletRequest request) {
        this.privacy = privacy;
        this.export = export;
        this.consent = consent;
        this.administration = administration;
        this.request = request;
    }

    @Override
    public ResponseEntity<List<DataSubjectRequestRead>> listPrivacyRequests() {
        return respond(administration.listRequests(), 200);
    }

    @Override
    public ResponseEntity<List<PrivacyContactRead>> listPrivacyContacts() {
        return respond(administration.listContacts(), 200);
    }

    @Override
    public ResponseEntity<PrivacyContactRead> resolvePrivacyContact(
            long requestId,
            PrivacyContactResolve body
    ) {

        return respond(administration.resolveContact(requestId,
                                    body, CurrentUser.require()), 200);
    }

    @Override
    public ResponseEntity<DataSubjectRequestRead> resolvePrivacyRequest(
            long requestId,
            DataSubjectRequestResolve body
    ) {

        return respond(administration.resolveRequest(requestId,
                                    body, CurrentUser.require()), 200);
    }

    @Override
    public ResponseEntity<PrivacyContactReceipt> createPrivacyContact(
            PrivacyContactCreate body
    ) {
        return respond(privacy.createContact(body, CurrentUser.optional().orElse(null)), 201);
    }

    @Override
    public ResponseEntity<CookieConsentRead> getCookieConsent() {
        return respond(consent.state(request), 200);
    }

    @Override
    public ResponseEntity<CookieConsentRead> saveCookieConsent(
            CookieConsentChoice body
    ) {
        return saveConsent(body);
    }

    @Override
    public ResponseEntity<CookieConsentPolicy> getCookiePolicy() {
        return respond(consent.policy(), 200);
    }

    @Override
    public ResponseEntity<PersonalDataExportRead> exportPersonalData() {
        return respond(export.build(CurrentUser.require()), 200);
    }

    @Override
    public ResponseEntity<List<DataSubjectRequestRead>> listMyDataSubjectRequests() {
        return respond(privacy.listRequests(CurrentUser.require().id()), 200);
    }

    @Override
    public ResponseEntity<DataSubjectRequestRead> createDataSubjectRequest(
            DataSubjectRequestCreate body
    ) {
        return respond(privacy.createRequest(CurrentUser.require(), body), 201);
    }

    private ResponseEntity<CookieConsentRead> saveConsent(CookieConsentChoice choice) {
        AuthenticatedUser user = CurrentUser.optional().orElse(null);
        CookieConsentService.SavedConsent saved = consent.save(choice, request, user);
        return ResponseEntity.ok()
                .header(HttpHeaders.SET_COOKIE, saved.cookie().toString())
                .body(saved.body());
    }
}
