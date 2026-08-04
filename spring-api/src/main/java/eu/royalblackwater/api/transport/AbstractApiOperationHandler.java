package eu.royalblackwater.api.transport;

import java.util.Map;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ResponseEntity;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.BAD_REQUEST;

public abstract class AbstractApiOperationHandler implements ApiOperationHandler {
    @Override
    public final ResponseEntity<?> handle(
            String operationId,
            Map<String, Object> parameters,
            Object body,
            MultipartFile upload,
            int successStatus) {
        Object result = execute(operationId, parameters, body, upload);
        if (result instanceof ResponseEntity<?> response) {
            return response;
        }
        if (successStatus == 204) {
            return ResponseEntity.noContent().build();
        }
        return ResponseEntity.status(HttpStatusCode.valueOf(successStatus)).body(result);
    }

    protected abstract Object execute(
            String operationId,
            Map<String, Object> parameters,
            Object body,
            MultipartFile upload);

    protected static long longParameter(Map<String, Object> parameters, String name) {
        Object value = parameters.get(name);
        if (value instanceof Number number) {
            return number.longValue();
        }
        throw new ResponseStatusException(BAD_REQUEST, "Missing or invalid parameter: " + name);
    }

    protected static int intParameter(Map<String, Object> parameters, String name) {
        return Math.toIntExact(longParameter(parameters, name));
    }

    protected static String stringParameter(Map<String, Object> parameters, String name) {
        Object value = parameters.get(name);
        return value == null ? null : String.valueOf(value);
    }

    protected static boolean booleanParameter(Map<String, Object> parameters, String name, boolean fallback) {
        Object value = parameters.get(name);
        return value instanceof Boolean flag ? flag : fallback;
    }

    protected static <T> T body(Object body, Class<T> type) {
        if (!type.isInstance(body)) {
            throw new ResponseStatusException(BAD_REQUEST, "Invalid request body.");
        }
        return type.cast(body);
    }
}
