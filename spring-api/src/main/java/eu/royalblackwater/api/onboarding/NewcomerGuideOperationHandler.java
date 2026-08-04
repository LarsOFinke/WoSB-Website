package eu.royalblackwater.api.onboarding;

import eu.royalblackwater.api.contract.NewcomerGuideUpdate;
import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class NewcomerGuideOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS = Set.of(
            "read_newcomer_guide_api_newcomer_guide_get",
            "replace_newcomer_guide_api_newcomer_guide_put");
    private final NewcomerGuideService guide;

    public NewcomerGuideOperationHandler(NewcomerGuideService guide) { this.guide = guide; }
    @Override public Set<String> operations() { return OPERATIONS; }

    @Override
    protected Object execute(String operationId, Map<String, Object> parameters, Object requestBody,
                             MultipartFile upload) {
        CurrentUser.require();
        return switch (operationId) {
            case "read_newcomer_guide_api_newcomer_guide_get" -> guide.get();
            case "replace_newcomer_guide_api_newcomer_guide_put" -> guide.replace(
                    body(requestBody, NewcomerGuideUpdate.class), CurrentUser.require());
            default -> throw new IllegalStateException("Unsupported newcomer guide operation: " + operationId);
        };
    }
}
