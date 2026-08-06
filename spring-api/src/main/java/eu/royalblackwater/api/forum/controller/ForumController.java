package eu.royalblackwater.api.forum.controller;

import eu.royalblackwater.api.dto.ForumPostRead;
import eu.royalblackwater.api.dto.ForumThreadRead;
import eu.royalblackwater.api.dto.ForumThreadSummary;
import java.util.List;
import eu.royalblackwater.api.dto.ForumPostCreate;
import eu.royalblackwater.api.dto.ForumPostUpdate;
import eu.royalblackwater.api.dto.ForumThreadCreate;
import eu.royalblackwater.api.dto.ForumThreadUpdate;
import eu.royalblackwater.api.contract.api.ForumApi;
import eu.royalblackwater.api.forum.service.ForumService;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import eu.royalblackwater.api.shared.filter.ListFilter;
import eu.royalblackwater.api.shared.web.ApiControllerSupport;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
public class ForumController extends ApiControllerSupport implements ForumApi {

    private final ForumService forum;

    public ForumController(ForumService forum) {
        this.forum = forum;
    }

    @Override
    public ResponseEntity<Void> deleteForumPost(
            long postId
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        forum.deletePost(postId, actor);
        return noContent();
    }

    @Override
    public ResponseEntity<ForumPostRead> putPost(
            long postId,
            ForumPostUpdate body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(forum.updatePost(
                            postId, body, actor), 200);
    }

    @Override
    public ResponseEntity<List<ForumThreadSummary>> getThreads(
            String search,
            String category,
            long limit,
            long offset
    ) {
        CurrentUser.require();
        ListFilter page = ListFilter.of(search, limit, offset, 100);
        return respond(forum.list(page.search(),
                ListFilter.optionalText(category, "category", 80),
                page.limit(), page.offset()), 200);
    }

    @Override
    public ResponseEntity<ForumThreadRead> postThread(
            ForumThreadCreate body
    ) {
        AuthenticatedUser actor = CurrentUser.require();
        return respond(forum.create(
                            body, actor), 201);
    }

    @Override
    public ResponseEntity<ForumThreadRead> getThreadDetail(
            long threadId
    ) {

        CurrentUser.require();
        return respond(forum.get(
                            threadId), 200);
    }

    @Override
    public ResponseEntity<ForumThreadRead> putThread(
            long threadId,
            ForumThreadUpdate body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(forum.updateThread(
                            threadId, body, actor), 200);
    }

    @Override
    public ResponseEntity<ForumPostRead> postReply(
            long threadId,
            ForumPostCreate body
    ) {

        AuthenticatedUser actor = CurrentUser.require();
        return respond(forum.addPost(
                            threadId, body, actor), 201);
    }
}
