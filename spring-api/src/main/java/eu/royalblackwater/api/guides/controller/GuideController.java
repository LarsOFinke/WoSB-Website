package eu.royalblackwater.api.guides.controller;

import eu.royalblackwater.api.dto.GuideCreate;
import eu.royalblackwater.api.dto.GuideRead;
import eu.royalblackwater.api.dto.GuideSummary;
import eu.royalblackwater.api.dto.GuideUpdate;
import eu.royalblackwater.api.guides.service.GuideService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.filter.ListFilter;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class GuideController extends ApiControllerSupport {

    private final GuideService guides;

    public GuideController(GuideService guides) { this.guides = guides; }

    @GetMapping("/api/guides")
    public ResponseEntity<List<GuideSummary>> getGuides(
            @RequestParam(name = "search", required = false) String search,
            @RequestParam(name = "category", required = false) String category,
            @RequestParam(name = "limit", defaultValue = "50") long limit,
            @RequestParam(name = "offset", defaultValue = "0") long offset
    ) {
        AuthenticatedUser actor = CurrentUser.require();
        ListFilter page = ListFilter.of(search, limit, offset, 100);
        return respond(guides.list(page.search(),
                ListFilter.optionalText(category, "category", 80),
                page.limit(), page.offset(), actor), 200);
    }

    @PostMapping("/api/guides")
    public ResponseEntity<GuideRead> postGuide(
            @Valid @RequestBody GuideCreate body
    ) {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(guides.create(body, actor), 201);
    }

    @DeleteMapping("/api/guides/{guide_id}")
    public ResponseEntity<Void> deleteOwnGuide(
            @PathVariable("guide_id") long guideId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        guides.delete(guideId, actor, false); return noContent();
    }

    @GetMapping("/api/guides/{guide_id}")
    public ResponseEntity<GuideRead> getGuideDetail(
            @PathVariable("guide_id") long guideId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(guides.get(guideId, actor), 200);
    }

    @PutMapping("/api/guides/{guide_id}")
    public ResponseEntity<GuideRead> putGuide(
            @PathVariable("guide_id") long guideId,
            @Valid @RequestBody GuideUpdate body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(guides.update(guideId, body, actor), 200);
    }
}
