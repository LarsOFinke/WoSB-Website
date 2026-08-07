package eu.royalblackwater.api.onboarding.controller;

import eu.royalblackwater.api.dto.NewcomerGuideRead;
import eu.royalblackwater.api.dto.NewcomerGuideUpdate;
import eu.royalblackwater.api.onboarding.service.NewcomerGuideService;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class NewcomerGuideController extends ApiControllerSupport {

    private final NewcomerGuideService guide;

    public NewcomerGuideController(NewcomerGuideService guide) { this.guide = guide; }

    @GetMapping("/api/newcomer-guide")
    public ResponseEntity<NewcomerGuideRead> readNewcomerGuide() {
        CurrentUser.require();
        return respond(guide.get(), 200);
    }

    @PutMapping("/api/newcomer-guide")
    public ResponseEntity<NewcomerGuideRead> replaceNewcomerGuide(
            @Valid @RequestBody NewcomerGuideUpdate body
    ) {
        CurrentUser.require();
        return respond(guide.replace(
                            body, CurrentUser.require()), 200);
    }
}
