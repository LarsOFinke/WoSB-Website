package eu.royalblackwater.api.legal;

import eu.royalblackwater.api.contract.LegalNoticeUpdate;
import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class LegalOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS = Set.of(
            "public_legal_notice_api_legal_notice_get",
            "admin_get_legal_notice_api_admin_legal_notice_get",
            "admin_update_legal_notice_api_admin_legal_notice_put",
            "admin_reset_legal_notice_api_admin_legal_notice_reset_environment_post");
    private final LegalNoticeService notices;

    public LegalOperationHandler(LegalNoticeService notices) {
        this.notices = notices;
    }

    @Override
    public Set<String> operations() { return OPERATIONS; }

    @Override
    protected Object execute(String operationId, Map<String, Object> parameters, Object body, MultipartFile upload) {
        return switch (operationId) {
            case "public_legal_notice_api_legal_notice_get" -> notices.publicNotice();
            case "admin_get_legal_notice_api_admin_legal_notice_get" -> notices.adminNotice();
            case "admin_update_legal_notice_api_admin_legal_notice_put" ->
                    notices.update(body(body, LegalNoticeUpdate.class), CurrentUser.require());
            case "admin_reset_legal_notice_api_admin_legal_notice_reset_environment_post" ->
                    notices.reset(CurrentUser.require());
            default -> throw new IllegalStateException("Unsupported legal operation: " + operationId);
        };
    }
}
