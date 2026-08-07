package eu.royalblackwater.api.guides.controller;

import eu.royalblackwater.api.dto.GuideSummary;
import eu.royalblackwater.api.guides.service.GuideService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.filter.ListFilter;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class GuideAdministrationController extends ApiControllerSupport {

    private final GuideService guides;

    public GuideAdministrationController(GuideService guides) { this.guides = guides; }

    @GetMapping("/api/admin/guides")
    public ResponseEntity<List<GuideSummary>> adminListGuides(
            @RequestParam(name = "search", required = false) String search,
            @RequestParam(name = "category", required = false) String category,
            @RequestParam(name = "limit", defaultValue = "50") long limit,
            @RequestParam(name = "offset", defaultValue = "0") long offset
    ) {
        CurrentUser.require();
        ListFilter page = ListFilter.of(search, limit, offset, 100);
        ListFilter.optionalText(category, "category", 80);
        return respond(guides.listForAdministration(page.limit(), page.offset()), 200);
    }

    @DeleteMapping("/api/admin/guides/{guide_id}")
    public ResponseEntity<Void> adminDeleteGuide(
            @PathVariable("guide_id") long guideId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        guides.delete(guideId, actor, true); return noContent();
    }
}
