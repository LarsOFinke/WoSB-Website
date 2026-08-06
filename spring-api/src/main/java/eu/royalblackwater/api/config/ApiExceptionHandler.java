package eu.royalblackwater.api.config;

import jakarta.servlet.http.HttpServletRequest;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
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

    @ExceptionHandler(Exception.class)
    ResponseEntity<Map<String, String>> unexpected(Exception exception, HttpServletRequest request) {
        LOG.error("api_error status=500 method={} path={} type={}",
                request.getMethod(), request.getRequestURI(), exception.getClass().getSimpleName(), exception);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("detail", "Internal server error."));
    }

    private static String safeReason(String reason) {
        if (reason == null || reason.isBlank()) return "unspecified";
        String normalized = reason.replaceAll("[\\r\\n\\t]", " ");
        return normalized.substring(0, Math.min(normalized.length(), 240));
    }
}
