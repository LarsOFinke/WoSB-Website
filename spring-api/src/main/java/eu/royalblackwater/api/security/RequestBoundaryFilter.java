package eu.royalblackwater.api.security;

import eu.royalblackwater.api.config.SecurityProperties;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.net.URI;
import java.util.Locale;
import java.util.Set;
import java.util.stream.Collectors;
import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
public class RequestBoundaryFilter extends OncePerRequestFilter {
    private static final Set<String> SAFE_METHODS = Set.of("GET", "HEAD", "OPTIONS");
    private final Set<String> allowedHosts;
    private final Set<String> allowedOrigins;

    public RequestBoundaryFilter(SecurityProperties properties) {
        allowedHosts = normalize(properties.allowedHosts());
        allowedOrigins = properties.allowedOrigins().stream().map(String::strip)
                .filter(value -> !value.isEmpty()).collect(Collectors.toUnmodifiableSet());
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        if (!allowedHosts.contains(request.getServerName().toLowerCase(Locale.ROOT))) {
            response.sendError(HttpServletResponse.SC_BAD_REQUEST);
            return;
        }
        if (!SAFE_METHODS.contains(request.getMethod()) && crossSite(request)) {
            response.sendError(HttpServletResponse.SC_FORBIDDEN);
            return;
        }
        chain.doFilter(request, response);
    }

    private boolean crossSite(HttpServletRequest request) {
        String fetchSite = request.getHeader("Sec-Fetch-Site");
        String origin = request.getHeader("Origin");
        if (origin != null && !origin.isBlank()) {
            try {
                URI parsed = URI.create(origin);
                String normalized = (parsed.getScheme() + "://" + parsed.getAuthority())
                        .toLowerCase(Locale.ROOT);
                return !allowedOrigins.contains(normalized);
            } catch (IllegalArgumentException exception) {
                return true;
            }
        }
        return fetchSite != null && "cross-site".equalsIgnoreCase(fetchSite);
    }

    private static Set<String> normalize(java.util.List<String> values) {
        return values.stream().map(String::strip).filter(value -> !value.isEmpty())
                .map(value -> value.split(":", 2)[0].toLowerCase(Locale.ROOT))
                .collect(Collectors.toUnmodifiableSet());
    }
}
