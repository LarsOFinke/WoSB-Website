package eu.royalblackwater.api.shared.web;

import jakarta.servlet.http.HttpServletRequest;
import java.util.regex.Pattern;
import org.springframework.web.servlet.HandlerMapping;

/** Shared, payload-free HTTP request context used by diagnostics and error boundaries. */
public final class ApiRequestAttributes {
    public static final String REQUEST_ID_HEADER = "X-Request-Id";
    private static final String REQUEST_ID_ATTRIBUTE = ApiRequestAttributes.class.getName() + ".requestId";
    private static final Pattern NUMERIC_SEGMENT = Pattern.compile("(?<=/)\\d+(?=/|$)");
    private static final Pattern UUID_SEGMENT = Pattern.compile(
            "(?<=/)[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}(?=/|$)");
    private static final Pattern BUILD_ROLE_SLUG = Pattern.compile("(?<=/api/admin/build-roles/)[^/]+(?=/|$)");

    private ApiRequestAttributes() { }

    public static void setRequestId(HttpServletRequest request, String requestId) {
        request.setAttribute(REQUEST_ID_ATTRIBUTE, requestId);
    }

    public static String requestId(HttpServletRequest request) {
        Object value = request.getAttribute(REQUEST_ID_ATTRIBUTE);
        return value instanceof String requestId && !requestId.isBlank() ? requestId : "unassigned";
    }

    public static String route(HttpServletRequest request) {
        Object route = request.getAttribute(HandlerMapping.BEST_MATCHING_PATTERN_ATTRIBUTE);
        if (route instanceof String pattern && !pattern.isBlank()) return pattern;
        return safePath(request.getRequestURI());
    }

    public static String safePath(String requestUri) {
        if (requestUri == null || requestUri.isBlank()) return "/";
        String normalized = UUID_SEGMENT.matcher(NUMERIC_SEGMENT.matcher(requestUri).replaceAll("{id}"))
                .replaceAll("{id}");
        return BUILD_ROLE_SLUG.matcher(normalized).replaceAll("{id}");
    }
}
