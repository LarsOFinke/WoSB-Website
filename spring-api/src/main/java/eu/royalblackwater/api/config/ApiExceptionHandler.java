package eu.royalblackwater.api.config;

import jakarta.servlet.http.HttpServletRequest;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.ErrorResponse;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.multipart.MaxUploadSizeExceededException;
import org.springframework.web.multipart.MultipartException;
import org.springframework.web.server.ResponseStatusException;

@RestControllerAdvice
public class ApiExceptionHandler {
    private static final Logger LOG = LoggerFactory.getLogger(ApiExceptionHandler.class);

    @ExceptionHandler(ResponseStatusException.class)
    ResponseEntity<Map<String, String>> status(ResponseStatusException exception, HttpServletRequest request) {
        int status = exception.getStatusCode().value();
        LOG.warn("api_error status={} method={} path={} type={} reason={}", status,
                request.getMethod(), request.getRequestURI(), exception.getClass().getSimpleName(),
                safeReason(exception.getReason()));
        return ResponseEntity.status(exception.getStatusCode())
                .body(Map.of("detail", exception.getReason() == null ? "Request rejected." : exception.getReason()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    ResponseEntity<Map<String, String>> validation(MethodArgumentNotValidException exception,
                                                    HttpServletRequest request) {
        String detail = exception.getBindingResult().getAllErrors().stream()
                .findFirst().map(error -> error.getDefaultMessage()).orElse("Invalid request.");
        LOG.warn("api_error status=400 method={} path={} type={} reason={}",
                request.getMethod(), request.getRequestURI(), exception.getClass().getSimpleName(), safeReason(detail));
        return ResponseEntity.badRequest().body(Map.of("detail", detail));
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    ResponseEntity<Map<String, String>> unreadable(HttpMessageNotReadableException exception,
                                                    HttpServletRequest request) {
        LOG.warn("api_error status=400 method={} path={} type={} reason={}",
                request.getMethod(), request.getRequestURI(), exception.getClass().getSimpleName(),
                safeReason(exception.getMostSpecificCause().getMessage()));
        return ResponseEntity.badRequest().body(Map.of("detail", "Request body is invalid."));
    }

    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    ResponseEntity<Map<String, String>> typeMismatch(MethodArgumentTypeMismatchException exception,
                                                      HttpServletRequest request) {
        LOG.warn("api_error status=400 method={} path={} type={} reason={}",
                request.getMethod(), request.getRequestURI(), exception.getClass().getSimpleName(),
                safeReason("Invalid query parameter: " + exception.getName()));
        return ResponseEntity.badRequest().body(Map.of("detail", "Query parameter is invalid."));
    }

    @ExceptionHandler(MaxUploadSizeExceededException.class)
    ResponseEntity<Map<String, String>> uploadTooLarge(MaxUploadSizeExceededException exception,
                                                        HttpServletRequest request) {
        LOG.warn("api_error status=413 method={} path={} type={} reason={}",
                request.getMethod(), request.getRequestURI(), exception.getClass().getSimpleName(),
                safeReason(exception.getMessage()));
        return ResponseEntity.status(HttpStatus.CONTENT_TOO_LARGE)
                .body(Map.of("detail", "Request body is too large."));
    }

    @ExceptionHandler(MultipartException.class)
    ResponseEntity<Map<String, String>> multipart(MultipartException exception, HttpServletRequest request) {
        LOG.warn("api_error status=400 method={} path={} type={} reason={}",
                request.getMethod(), request.getRequestURI(), exception.getClass().getSimpleName(),
                safeReason(exception.getMessage()));
        return ResponseEntity.badRequest().body(Map.of("detail", "Multipart request is invalid."));
    }

    @ExceptionHandler(Exception.class)
    ResponseEntity<Map<String, String>> unexpected(Exception exception, HttpServletRequest request) {
        if (exception instanceof ErrorResponse errorResponse && errorResponse.getStatusCode().is4xxClientError()) {
            int status = errorResponse.getStatusCode().value();
            LOG.warn("api_error status={} method={} path={} type={} reason={}", status,
                    request.getMethod(), request.getRequestURI(), exception.getClass().getSimpleName(),
                    safeReason(errorResponse.getBody().getDetail()));
            return ResponseEntity.status(errorResponse.getStatusCode())
                    .body(Map.of("detail", clientErrorDetail(status)));
        }
        LOG.error("api_error status=500 method={} path={} type={}",
                request.getMethod(), request.getRequestURI(), exception.getClass().getSimpleName(), exception);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("detail", "Internal server error."));
    }

    private static String clientErrorDetail(int status) {
        return switch (status) {
            case 400 -> "Request is invalid.";
            case 404 -> "Resource not found.";
            case 405 -> "HTTP method is not supported.";
            case 413 -> "Request body is too large.";
            case 415 -> "Content type is not supported.";
            default -> "Request rejected.";
        };
    }

    private static String safeReason(String reason) {
        if (reason == null || reason.isBlank()) return "unspecified";
        String normalized = reason.replaceAll("[\\r\\n\\t]", " ");
        return normalized.substring(0, Math.min(normalized.length(), 240));
    }
}
