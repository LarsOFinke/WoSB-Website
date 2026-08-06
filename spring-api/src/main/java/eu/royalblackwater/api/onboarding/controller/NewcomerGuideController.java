package eu.royalblackwater.api.onboarding.controller;

import eu.royalblackwater.api.dto.NewcomerGuideRead;
import eu.royalblackwater.api.dto.NewcomerGuideUpdate;
import eu.royalblackwater.api.contract.api.NewcomerGuideApi;
import eu.royalblackwater.api.onboarding.service.NewcomerGuideService;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class NewcomerGuideController extends ApiControllerSupport implements NewcomerGuideApi {

    private final NewcomerGuideService guide;

    public NewcomerGuideController(NewcomerGuideService guide) { this.guide = guide; }

    @Override
    public ResponseEntity<NewcomerGuideRead> readNewcomerGuide() {
        CurrentUser.require();
        return respond(guide.get(), 200);
    }

    @Override
    public ResponseEntity<NewcomerGuideRead> replaceNewcomerGuide(
            NewcomerGuideUpdate body
    ) {
        CurrentUser.require();
        return respond(guide.replace(
                            body, CurrentUser.require()), 200);
    }
}
