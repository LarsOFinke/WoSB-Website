package eu.royalblackwater.api.forum.controller;

import eu.royalblackwater.api.dto.ForumPostCreate;
import eu.royalblackwater.api.dto.ForumPostRead;
import eu.royalblackwater.api.dto.ForumPostUpdate;
import eu.royalblackwater.api.dto.ForumThreadCreate;
import eu.royalblackwater.api.dto.ForumThreadRead;
import eu.royalblackwater.api.dto.ForumThreadSummary;
import eu.royalblackwater.api.dto.ForumThreadUpdate;
import eu.royalblackwater.api.forum.service.ForumService;
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
public class ForumController extends ApiControllerSupport {

    private final ForumService forum;

    public ForumController(ForumService forum) {
        this.forum = forum;
    }

    @DeleteMapping("/api/forum/posts/{post_id}")
    public ResponseEntity<Void> deleteForumPost(
            @PathVariable("post_id") long postId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        forum.deletePost(postId, actor);
        return noContent();
    }

    @PutMapping("/api/forum/posts/{post_id}")
    public ResponseEntity<ForumPostRead> putPost(
            @PathVariable("post_id") long postId,
            @Valid @RequestBody ForumPostUpdate body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(forum.updatePost(
                            postId, body, actor), 200);
    }

    @GetMapping("/api/forum/threads")
    public ResponseEntity<List<ForumThreadSummary>> getThreads(
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

    @PostMapping("/api/forum/threads")
    public ResponseEntity<ForumThreadRead> postThread(
            @Valid @RequestBody ForumThreadCreate body
    ) {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(forum.create(
                            body, actor), 201);
    }

    @GetMapping("/api/forum/threads/{thread_id}")
    public ResponseEntity<ForumThreadRead> getThreadDetail(
            @PathVariable("thread_id") long threadId
    ) {

        CurrentUser.require();
        return respond(forum.get(
                            threadId), 200);
    }

    @PutMapping("/api/forum/threads/{thread_id}")
    public ResponseEntity<ForumThreadRead> putThread(
            @PathVariable("thread_id") long threadId,
            @Valid @RequestBody ForumThreadUpdate body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(forum.updateThread(
                            threadId, body, actor), 200);
    }

    @PostMapping("/api/forum/threads/{thread_id}/posts")
    public ResponseEntity<ForumPostRead> postReply(
            @PathVariable("thread_id") long threadId,
            @Valid @RequestBody ForumPostCreate body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(forum.addPost(
                            threadId, body, actor), 201);
    }
}
