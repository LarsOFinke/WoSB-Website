package eu.royalblackwater.api.guides;

import eu.royalblackwater.api.security.AuthenticatedUser;
import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class GuideAdministrationOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS = Set.of(
            "admin_list_guides_api_admin_guides_get", "admin_delete_guide_api_admin_guides__guide_id__delete");
    private final GuideService guides;

    public GuideAdministrationOperationHandler(GuideService guides) { this.guides = guides; }
    @Override public Set<String> operations() { return OPERATIONS; }

    @Override
    protected Object execute(String operationId, Map<String, Object> parameters, Object requestBody, MultipartFile upload) {
        AuthenticatedUser actor = CurrentUser.require();
        return switch (operationId) {
            case "admin_list_guides_api_admin_guides_get" -> guides.listForAdministration();
            case "admin_delete_guide_api_admin_guides__guide_id__delete" -> { guides.delete(longParameter(parameters, "guide_id"), actor, true); yield null; }
            default -> throw new IllegalStateException("Unsupported guide administration operation: " + operationId);
        };
    }
}
