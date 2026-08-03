package eu.royalblackwater.api.proxy;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.net.ConnectException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Collections;
import java.util.Set;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** Transitional HTTP facade while FastAPI remains the domain owner. */
@RestController
public class FastApiProxyController {
    private static final Set<String> REQUEST_HEADERS = Set.of(
            "accept", "accept-encoding", "content-type", "cookie", "if-match", "if-modified-since",
            "if-none-match", "if-unmodified-since", "range", "user-agent", "x-csrf-token",
            "origin", "referer", "sec-fetch-site", "sec-fetch-mode", "sec-fetch-dest",
            "x-forwarded-for", "x-forwarded-host", "x-forwarded-proto", "x-real-ip");
    private static final Set<String> RESPONSE_HEADERS = Set.of(
            "cache-control", "content-disposition", "content-type", "etag", "expires", "last-modified",
            "content-encoding", "location", "retry-after", "set-cookie", "vary", "www-authenticate",
            "x-robots-tag");

    private final URI target;
    private final HttpClient client;

    public FastApiProxyController(@Value("${rbf.proxy.target-url:http://api:8000}") String targetUrl) {
        this.target = URI.create(targetUrl.endsWith("/") ? targetUrl.substring(0, targetUrl.length() - 1) : targetUrl);
        this.client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(5))
                .followRedirects(HttpClient.Redirect.NEVER)
                .build();
    }

    @RequestMapping({"/api", "/api/{*path}"})
    public void proxy(HttpServletRequest request, HttpServletResponse response) throws IOException {
        URI destination = target.resolve(request.getRequestURI().substring(request.getContextPath().length())
                + (request.getQueryString() == null ? "" : "?" + request.getQueryString()));
        HttpRequest.BodyPublisher publisher = switch (request.getMethod()) {
            case "GET", "HEAD" -> HttpRequest.BodyPublishers.noBody();
            default -> HttpRequest.BodyPublishers.ofInputStream(() -> {
                try {
                    return request.getInputStream();
                } catch (IOException exception) {
                    throw new java.io.UncheckedIOException(exception);
                }
            });
        };
        HttpRequest.Builder builder = HttpRequest.newBuilder(destination)
                .timeout(Duration.ofSeconds(130))
                .method(request.getMethod(), publisher);
        copyRequestHeaders(request, builder);
        try {
            HttpResponse<java.io.InputStream> upstream = client.send(builder.build(), HttpResponse.BodyHandlers.ofInputStream());
            response.setStatus(upstream.statusCode());
            copyResponseHeaders(upstream, response);
            try (var upstreamBody = upstream.body()) {
                upstreamBody.transferTo(response.getOutputStream());
            }
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new IOException("FastAPI proxy request interrupted.", exception);
        } catch (java.net.http.HttpTimeoutException exception) {
            response.sendError(HttpStatus.GATEWAY_TIMEOUT.value());
        } catch (ConnectException exception) {
            response.sendError(HttpStatus.BAD_GATEWAY.value());
        }
    }

    private static void copyRequestHeaders(HttpServletRequest request, HttpRequest.Builder builder) {
        Collections.list(request.getHeaderNames()).stream()
                .filter(name -> REQUEST_HEADERS.contains(name.toLowerCase()))
                .forEach(name -> Collections.list(request.getHeaders(name))
                        .forEach(value -> builder.header(name, value)));
        String host = request.getHeader("Host");
        if (host != null && !host.isBlank()) builder.header("X-Forwarded-Host", host);
        builder.header("X-Forwarded-Proto", request.getScheme());
        builder.header("X-Forwarded-For", request.getRemoteAddr());
    }

    private static void copyResponseHeaders(HttpResponse<?> upstream, HttpServletResponse response) {
        upstream.headers().map().forEach((name, values) -> {
            if (RESPONSE_HEADERS.contains(name.toLowerCase())) values.forEach(value -> response.addHeader(name, value));
        });
    }
}
