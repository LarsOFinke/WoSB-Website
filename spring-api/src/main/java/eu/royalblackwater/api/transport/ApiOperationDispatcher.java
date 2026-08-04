package eu.royalblackwater.api.transport;

import jakarta.annotation.PostConstruct;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
public class ApiOperationDispatcher {
    private final List<ApiOperationHandler> handlers;
    private Map<String, ApiOperationHandler> byOperation = Map.of();

    public ApiOperationDispatcher(List<ApiOperationHandler> handlers) {
        this.handlers = List.copyOf(handlers);
    }

    @PostConstruct
    void verifyCoverage() {
        Map<String, ApiOperationHandler> registered = new HashMap<>();
        for (ApiOperationHandler handler : handlers) {
            for (String operation : handler.operations()) {
                ApiOperationHandler previous = registered.putIfAbsent(operation, handler);
                if (previous != null) {
                    throw new IllegalStateException("Duplicate API operation handler: " + operation);
                }
            }
        }
        var missing = ApiOperationCatalog.ALL.stream().filter(operation -> !registered.containsKey(operation)).sorted().toList();
        var unknown = registered.keySet().stream().filter(operation -> !ApiOperationCatalog.ALL.contains(operation)).sorted().toList();
        if (!missing.isEmpty() || !unknown.isEmpty()) {
            throw new IllegalStateException("API operation coverage mismatch; missing=" + missing + ", unknown=" + unknown);
        }
        byOperation = Map.copyOf(registered);
    }

    public ResponseEntity<?> dispatch(
            String operationId,
            Map<String, Object> parameters,
            Object body,
            MultipartFile upload,
            int successStatus) {
        ApiOperationHandler handler = byOperation.get(operationId);
        if (handler == null) {
            throw new IllegalStateException("No API operation handler: " + operationId);
        }
        return handler.handle(operationId, parameters, body, upload, successStatus);
    }
}
