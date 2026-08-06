package eu.royalblackwater.api.forum.controller;

import eu.royalblackwater.api.dto.ForumThreadSummary;
import java.util.List;
import eu.royalblackwater.api.contract.api.AdminForumApi;
import eu.royalblackwater.api.forum.service.ForumService;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.filter.ListFilter;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import eu.royalblackwater.api.shared.web.RequestParameters;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class ForumAdministrationController extends ApiControllerSupport implements AdminForumApi {

    private final ForumService forum;

    public ForumAdministrationController(ForumService forum) {
        this.forum = forum;
    }

    @Override
    public ResponseEntity<List<ForumThreadSummary>> adminListForumThreads(
            String search,
            String category,
            long limit,
            long offset
    ) {
        Map<String, Object> parameters = RequestParameters.of("search", search, "category", category, "limit", limit, "offset", offset);
        ListFilter page = ListFilter.from(parameters, 50, 100);
        return respond(forum.list(ListFilter.optionalText(parameters, "search", 120),
                ListFilter.optionalText(parameters, "category", 80), page.limit(), page.offset()), 200);
    }

    @Override
    public ResponseEntity<Void> adminDeleteForumThread(
            long threadId
    ) {

        forum.deleteThread(threadId,CurrentUser.require());
        return noContent();
    }
}
