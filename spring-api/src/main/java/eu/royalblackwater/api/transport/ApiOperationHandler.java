package eu.royalblackwater.api.transport;

import java.util.Map;
import java.util.Set;
import org.springframework.http.ResponseEntity;
import org.springframework.web.multipart.MultipartFile;

public interface ApiOperationHandler {
    Set<String> operations();

    ResponseEntity<?> handle(
            String operationId,
            Map<String, Object> parameters,
            Object body,
            MultipartFile upload,
            int successStatus);
}
