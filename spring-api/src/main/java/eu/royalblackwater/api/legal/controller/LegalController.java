package eu.royalblackwater.api.legal.controller;

import eu.royalblackwater.api.dto.LegalNoticeAdminRead;
import eu.royalblackwater.api.dto.LegalNoticePublicRead;
import eu.royalblackwater.api.dto.LegalNoticeUpdate;
import eu.royalblackwater.api.legal.service.LegalNoticeService;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class LegalController extends ApiControllerSupport {

    private final LegalNoticeService notices;

    public LegalController(LegalNoticeService notices) {
        this.notices = notices;
    }

    @GetMapping("/api/admin/legal-notice")
    public ResponseEntity<LegalNoticeAdminRead> adminGetLegalNotice() {
        return respond(notices.adminNotice(), 200);
    }

    @PutMapping("/api/admin/legal-notice")
    public ResponseEntity<LegalNoticeAdminRead> adminUpdateLegalNotice(
            @Valid @RequestBody LegalNoticeUpdate body
    ) {
        return respond(notices.update(body, CurrentUser.require()), 200);
    }

    @PostMapping("/api/admin/legal-notice/reset-environment")
    public ResponseEntity<LegalNoticeAdminRead> adminResetLegalNotice() {
        return respond(notices.reset(CurrentUser.require()), 200);
    }

    @GetMapping("/api/legal-notice")
    public ResponseEntity<LegalNoticePublicRead> publicLegalNotice() {
        return respond(notices.publicNotice(), 200);
    }
}
