package eu.royalblackwater.api.forum;

import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import eu.royalblackwater.api.transport.ListFilter;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class ForumAdministrationOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS = Set.of(
            "admin_list_forum_threads_api_admin_forum_threads_get",
            "admin_delete_forum_thread_api_admin_forum_threads__thread_id__delete");
    private final ForumService forum;

    public ForumAdministrationOperationHandler(ForumService forum) {
        this.forum = forum;
    }

    @Override
    public Set<String> operations() { return OPERATIONS; }

    @Override
    protected Object execute(String operationId, Map<String, Object> parameters, Object body, MultipartFile upload) {
        return switch (operationId) {
            case "admin_list_forum_threads_api_admin_forum_threads_get" ->
                    forum.list(ListFilter.optionalText(parameters, "search", 120),
                            ListFilter.optionalText(parameters, "category", 80));
            case "admin_delete_forum_thread_api_admin_forum_threads__thread_id__delete" -> {
                forum.deleteThread(longParameter(parameters,"thread_id"),CurrentUser.require());
                yield null;
            }
            default -> throw new IllegalStateException("Unsupported forum administration operation: " + operationId);
        };
    }
}
