package eu.royalblackwater.api.forum.controller;

import eu.royalblackwater.api.dto.ForumThreadSummary;
import eu.royalblackwater.api.forum.service.ForumService;
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
public class ForumAdministrationController extends ApiControllerSupport {

    private final ForumService forum;

    public ForumAdministrationController(ForumService forum) {
        this.forum = forum;
    }

    @GetMapping("/api/admin/forum/threads")
    public ResponseEntity<List<ForumThreadSummary>> adminListForumThreads(
            @RequestParam(name = "search", required = false) String search,
            @RequestParam(name = "category", required = false) String category,
            @RequestParam(name = "limit", defaultValue = "50") long limit,
            @RequestParam(name = "offset", defaultValue = "0") long offset
    ) {
        CurrentUser.require();
        ListFilter page = ListFilter.of(search, limit, offset, 100);
        return respond(forum.list(page.search(),
                ListFilter.optionalText(category, "category", 80),
                page.limit(), page.offset()), 200);
    }

    @DeleteMapping("/api/admin/forum/threads/{thread_id}")
    public ResponseEntity<Void> adminDeleteForumThread(
            @PathVariable("thread_id") long threadId
    ) {

        forum.deleteThread(threadId,CurrentUser.require());
        return noContent();
    }
}
