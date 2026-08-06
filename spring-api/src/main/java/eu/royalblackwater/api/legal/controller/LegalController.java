package eu.royalblackwater.api.legal.controller;

import eu.royalblackwater.api.dto.LegalNoticeAdminRead;
import eu.royalblackwater.api.dto.LegalNoticePublicRead;
import eu.royalblackwater.api.dto.LegalNoticeUpdate;
import eu.royalblackwater.api.contract.api.AdminLegalNoticeApi;
import eu.royalblackwater.api.contract.api.LegalNoticeApi;
import eu.royalblackwater.api.legal.service.LegalNoticeService;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class LegalController extends ApiControllerSupport implements AdminLegalNoticeApi, LegalNoticeApi {

    private final LegalNoticeService notices;

    public LegalController(LegalNoticeService notices) {
        this.notices = notices;
    }

    @Override
    public ResponseEntity<LegalNoticeAdminRead> adminGetLegalNotice() {
        return respond(notices.adminNotice(), 200);
    }

    @Override
    public ResponseEntity<LegalNoticeAdminRead> adminUpdateLegalNotice(
            LegalNoticeUpdate body
    ) {
        return respond(notices.update(body, CurrentUser.require()), 200);
    }

    @Override
    public ResponseEntity<LegalNoticeAdminRead> adminResetLegalNotice() {
        return respond(notices.reset(CurrentUser.require()), 200);
    }

    @Override
    public ResponseEntity<LegalNoticePublicRead> publicLegalNotice() {
        return respond(notices.publicNotice(), 200);
    }
}
