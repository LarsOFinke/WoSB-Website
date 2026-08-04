package eu.royalblackwater.api.forum;

import eu.royalblackwater.api.contract.ForumPostCreate;
import eu.royalblackwater.api.contract.ForumPostUpdate;
import eu.royalblackwater.api.contract.ForumThreadCreate;
import eu.royalblackwater.api.contract.ForumThreadUpdate;
import eu.royalblackwater.api.security.AuthenticatedUser;
import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import eu.royalblackwater.api.transport.ListFilter;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class ForumOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS = Set.of(
            "get_threads_api_forum_threads_get",
            "post_thread_api_forum_threads_post",
            "get_thread_detail_api_forum_threads__thread_id__get",
            "put_thread_api_forum_threads__thread_id__put",
            "post_reply_api_forum_threads__thread_id__posts_post",
            "put_post_api_forum_posts__post_id__put",
            "delete_forum_post_api_forum_posts__post_id__delete");
    private final ForumService forum;

    public ForumOperationHandler(ForumService forum) {
        this.forum = forum;
    }

    @Override
    public Set<String> operations() { return OPERATIONS; }

    @Override
    protected Object execute(String operationId, Map<String, Object> parameters, Object requestBody,
                             MultipartFile upload) {
        AuthenticatedUser actor = CurrentUser.require();
        return switch (operationId) {
            case "get_threads_api_forum_threads_get" -> forum.list(
                    ListFilter.optionalText(parameters, "search", 120),
                    ListFilter.optionalText(parameters, "category", 80));
            case "post_thread_api_forum_threads_post" -> forum.create(
                    body(requestBody, ForumThreadCreate.class), actor);
            case "get_thread_detail_api_forum_threads__thread_id__get" -> forum.get(
                    longParameter(parameters, "thread_id"));
            case "put_thread_api_forum_threads__thread_id__put" -> forum.updateThread(
                    longParameter(parameters, "thread_id"), body(requestBody, ForumThreadUpdate.class), actor);
            case "post_reply_api_forum_threads__thread_id__posts_post" -> forum.addPost(
                    longParameter(parameters, "thread_id"), body(requestBody, ForumPostCreate.class), actor);
            case "put_post_api_forum_posts__post_id__put" -> forum.updatePost(
                    longParameter(parameters, "post_id"), body(requestBody, ForumPostUpdate.class), actor);
            case "delete_forum_post_api_forum_posts__post_id__delete" -> {
                forum.deletePost(longParameter(parameters, "post_id"), actor);
                yield null;
            }
            default -> throw new IllegalStateException("Unsupported forum operation: " + operationId);
        };
    }
}
