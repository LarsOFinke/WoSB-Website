package eu.royalblackwater.api.guides.controller;

import eu.royalblackwater.api.dto.GuideSummary;
import java.util.List;
import eu.royalblackwater.api.contract.api.AdminGuidesApi;
import eu.royalblackwater.api.guides.service.GuideService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.filter.ListFilter;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class GuideAdministrationController extends ApiControllerSupport implements AdminGuidesApi {

    private final GuideService guides;

    public GuideAdministrationController(GuideService guides) { this.guides = guides; }

    @Override
    public ResponseEntity<List<GuideSummary>> adminListGuides(
            String search,
            String category,
            long limit,
            long offset
    ) {
        CurrentUser.require();
        ListFilter page = ListFilter.of(search, limit, offset, 100);
        ListFilter.optionalText(category, "category", 80);
        return respond(guides.listForAdministration(page.limit(), page.offset()), 200);
    }

    @Override
    public ResponseEntity<Void> adminDeleteGuide(
            long guideId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        guides.delete(guideId, actor, true); return noContent();
    }
}
