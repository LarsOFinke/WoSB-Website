package eu.royalblackwater.api.guides.controller;

import eu.royalblackwater.api.dto.GuideRead;
import eu.royalblackwater.api.dto.GuideSummary;
import java.util.List;
import eu.royalblackwater.api.dto.GuideCreate;
import eu.royalblackwater.api.dto.GuideUpdate;
import eu.royalblackwater.api.contract.api.GuidesApi;
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
public class GuideController extends ApiControllerSupport implements GuidesApi {

    private final GuideService guides;

    public GuideController(GuideService guides) { this.guides = guides; }

    @Override
    public ResponseEntity<List<GuideSummary>> getGuides(
            String search,
            String category,
            long limit,
            long offset
    ) {
        AuthenticatedUser actor = CurrentUser.require();
        ListFilter page = ListFilter.of(search, limit, offset, 100);
        return respond(guides.list(page.search(),
                ListFilter.optionalText(category, "category", 80),
                page.limit(), page.offset(), actor), 200);
    }

    @Override
    public ResponseEntity<GuideRead> postGuide(
            GuideCreate body
    ) {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(guides.create(body, actor), 201);
    }

    @Override
    public ResponseEntity<Void> deleteOwnGuide(
            long guideId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        guides.delete(guideId, actor, false); return noContent();
    }

    @Override
    public ResponseEntity<GuideRead> getGuideDetail(
            long guideId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(guides.get(guideId, actor), 200);
    }

    @Override
    public ResponseEntity<GuideRead> putGuide(
            long guideId,
            GuideUpdate body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(guides.update(guideId, body, actor), 200);
    }
}
