package eu.royalblackwater.api.shared.filter;

import eu.royalblackwater.api.config.ApiDiagnosticsProperties;
import eu.royalblackwater.api.shared.web.ApiRequestAttributes;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
@Order(Ordered.HIGHEST_PRECEDENCE + 10)
public class ApiRequestLoggingFilter extends OncePerRequestFilter {
    private static final Logger LOG = LoggerFactory.getLogger(ApiRequestLoggingFilter.class);
    private final ApiDiagnosticsProperties diagnostics;

    public ApiRequestLoggingFilter(ApiDiagnosticsProperties diagnostics) {
        this.diagnostics = diagnostics;
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String path = request.getRequestURI();
        return path == null || !path.startsWith("/api/");
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        String requestId = UUID.randomUUID().toString();
        ApiRequestAttributes.setRequestId(request, requestId);
        response.setHeader(ApiRequestAttributes.REQUEST_ID_HEADER, requestId);
        long started = System.nanoTime();
        try (MDC.MDCCloseable ignored = MDC.putCloseable("request_id", requestId)) {
            if (diagnostics.httpLifecycleLogging()) {
                LOG.info("api_request_start request_id={} method={} path={}", requestId,
                        request.getMethod(), ApiRequestAttributes.safePath(request.getRequestURI()));
            }
            try {
                chain.doFilter(request, response);
            } finally {
                if (diagnostics.httpLifecycleLogging()) {
                    long durationMillis = Math.max(0, (System.nanoTime() - started) / 1_000_000L);
                    LOG.info("api_request_complete request_id={} method={} path={} status={} duration_ms={}",
                            requestId, request.getMethod(), ApiRequestAttributes.route(request),
                            response.getStatus(), durationMillis);
                }
            }
        }
    }
}
