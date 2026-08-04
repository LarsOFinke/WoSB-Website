package eu.royalblackwater.api.files;

import eu.royalblackwater.api.security.AuthenticatedUser;
import eu.royalblackwater.api.security.CurrentUser;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class FileOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS = Set.of(
            "get_files_api_files_get",
            "post_file_api_files_post",
            "delete_own_file_api_files__file_id__delete",
            "get_file_content_api_files__file_id__content_get");
    private final FileAssetService files;

    public FileOperationHandler(FileAssetService files) {
        this.files = files;
    }

    @Override
    public Set<String> operations() { return OPERATIONS; }

    @Override
    protected Object execute(String operationId, Map<String, Object> parameters, Object requestBody,
                             MultipartFile upload) {
        return switch (operationId) {
            case "get_files_api_files_get" -> {
                AuthenticatedUser actor = CurrentUser.require();
                yield files.list(actor.id(), stringParameter(parameters, "usage_context"));
            }
            case "post_file_api_files_post" -> files.upload(
                    upload, stringParameter(parameters, "usage_context"), CurrentUser.require());
            case "delete_own_file_api_files__file_id__delete" -> {
                files.delete(longParameter(parameters, "file_id"), CurrentUser.require());
                yield null;
            }
            case "get_file_content_api_files__file_id__content_get" -> files.content(
                    longParameter(parameters, "file_id"), CurrentUser.optional().orElse(null));
            default -> throw new IllegalStateException("Unsupported file operation: " + operationId);
        };
    }
}
