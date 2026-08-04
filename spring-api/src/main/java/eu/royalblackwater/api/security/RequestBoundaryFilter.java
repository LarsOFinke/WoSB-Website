package eu.royalblackwater.api.security;

import eu.royalblackwater.api.config.SecurityProperties;
import eu.royalblackwater.api.securityops.IpBlockService;
import eu.royalblackwater.api.securityops.SecuritySignalService;
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
    private final IpBlockService ipBlocks;
    private final SecuritySignalService signals;

    public RequestBoundaryFilter(SecurityProperties properties, IpBlockService ipBlocks, SecuritySignalService signals) {
        allowedHosts = normalize(properties.allowedHosts());
        allowedOrigins = Set.copyOf(properties.normalizeOrigins());
        this.ipBlocks = ipBlocks;
        this.signals = signals;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        if (ipBlocks.isBlocked(request.getRemoteAddr())) {
            response.sendError(HttpServletResponse.SC_FORBIDDEN);
            return;
        }
        if (!allowedHosts.contains(request.getServerName().toLowerCase(Locale.ROOT))) {
            signals.record(request, "reconnaissance", "invalid_host");
            response.sendError(HttpServletResponse.SC_BAD_REQUEST);
            return;
        }
        if (!SAFE_METHODS.contains(request.getMethod()) && crossSite(request)) {
            signals.record(request, "reconnaissance", "cross_site");
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
                return !isSameOrigin(request, parsed) && !allowedOrigins.contains(normalized);
            } catch (IllegalArgumentException exception) {
                return true;
            }
        }
        return fetchSite != null && "cross-site".equalsIgnoreCase(fetchSite);
    }

    private static boolean isSameOrigin(HttpServletRequest request, URI origin) {
        if (origin.getHost() == null || !origin.getHost().equalsIgnoreCase(request.getServerName())) return false;
        String scheme = request.getScheme();
        if (scheme == null || !scheme.equalsIgnoreCase(origin.getScheme())) return false;
        int requestPort = effectivePort(scheme, request.getServerPort());
        int originPort = effectivePort(origin.getScheme(), origin.getPort());
        return requestPort == originPort;
    }

    private static int effectivePort(String scheme, int port) {
        if (port > 0) return port;
        return "https".equalsIgnoreCase(scheme) ? 443 : 80;
    }

    private static Set<String> normalize(java.util.List<String> values) {
        if (values == null) return Set.of();
        return values.stream().map(String::strip).filter(value -> !value.isEmpty())
                .map(value -> value.split(":", 2)[0].toLowerCase(Locale.ROOT))
                .collect(Collectors.toUnmodifiableSet());
    }
}
