package eu.royalblackwater.api.guides;

import eu.royalblackwater.api.contract.GuideCreate;
import eu.royalblackwater.api.contract.GuideUpdate;
import eu.royalblackwater.api.security.AuthenticatedUser;
import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import eu.royalblackwater.api.transport.ListFilter;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class GuideOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS = Set.of(
            "get_guides_api_guides_get", "post_guide_api_guides_post", "get_guide_detail_api_guides__guide_id__get",
            "put_guide_api_guides__guide_id__put", "delete_own_guide_api_guides__guide_id__delete");
    private final GuideService guides;

    public GuideOperationHandler(GuideService guides) { this.guides = guides; }
    @Override public Set<String> operations() { return OPERATIONS; }

    @Override
    protected Object execute(String operationId, Map<String, Object> parameters, Object requestBody, MultipartFile upload) {
        AuthenticatedUser actor = CurrentUser.require();
        return switch (operationId) {
            case "get_guides_api_guides_get" -> {
                ListFilter page = ListFilter.from(parameters, 50, 100);
                yield guides.list(ListFilter.optionalText(parameters, "search", 120),
                        ListFilter.optionalText(parameters, "category", 80), page.limit(), page.offset(), actor);
            }
            case "post_guide_api_guides_post" -> guides.create(body(requestBody, GuideCreate.class), actor);
            case "get_guide_detail_api_guides__guide_id__get" -> guides.get(longParameter(parameters, "guide_id"), actor);
            case "put_guide_api_guides__guide_id__put" -> guides.update(longParameter(parameters, "guide_id"), body(requestBody, GuideUpdate.class), actor);
            case "delete_own_guide_api_guides__guide_id__delete" -> { guides.delete(longParameter(parameters, "guide_id"), actor, false); yield null; }
            default -> throw new IllegalStateException("Unsupported guide operation: " + operationId);
        };
    }
}
