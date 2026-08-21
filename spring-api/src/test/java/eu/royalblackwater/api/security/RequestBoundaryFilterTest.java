package eu.royalblackwater.api.security;

import eu.royalblackwater.api.config.SecurityProperties;
import eu.royalblackwater.api.security.filter.RequestBoundaryFilter;
import eu.royalblackwater.api.securityops.service.IpBlockService;
import eu.royalblackwater.api.securityops.service.SecuritySignalService;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockFilterChain;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.never;

class RequestBoundaryFilterTest {
    private final IpBlockService ipBlocks = unblockedIpService();
    private final SecuritySignalService signals = mock(SecuritySignalService.class);
    private final RequestBoundaryFilter filter = filter(new SecurityProperties(
            List.of("app.example", "localhost"), List.of("https://app.example")));

    @Test
    void rejectsUntrustedHost() throws Exception {
        var request = request("GET", "attacker.example");
        var response = new MockHttpServletResponse();
        filter.doFilter(request, response, new MockFilterChain());
        assertThat(response.getStatus()).isEqualTo(400);
    }

    @Test
    void rejectsCrossSiteMutation() throws Exception {
        var request = request("POST", "app.example");
        request.addHeader("Origin", "https://attacker.example");
        request.addHeader("Sec-Fetch-Site", "cross-site");
        var response = new MockHttpServletResponse();
        filter.doFilter(request, response, new MockFilterChain());
        assertThat(response.getStatus()).isEqualTo(403);
    }

    @Test
    void permitsSameOriginMutation() throws Exception {
        var request = request("POST", "app.example");
        request.addHeader("Origin", "https://app.example");
        var response = new MockHttpServletResponse();
        filter.doFilter(request, response, new MockFilterChain());
        assertThat(response.getStatus()).isEqualTo(200);
    }

    @Test
    void permitsConfiguredCrossSiteMutation() throws Exception {
        var request = request("POST", "app.example");
        request.addHeader("Origin", "https://app.example");
        request.addHeader("Sec-Fetch-Site", "cross-site");
        var response = new MockHttpServletResponse();
        filter.doFilter(request, response, new MockFilterChain());
        assertThat(response.getStatus()).isEqualTo(200);
    }

    @Test
    void permitsSameOriginMutationWhenOriginListIsStale() throws Exception {
        var localFilter = filter(new SecurityProperties(List.of("app.example"), List.of()));
        var request = request("POST", "app.example");
        request.setScheme("http");
        request.setServerPort(80);
        request.addHeader("Origin", "http://app.example");
        var response = new MockHttpServletResponse();
        localFilter.doFilter(request, response, new MockFilterChain());
        assertThat(response.getStatus()).isEqualTo(200);
    }

    @Test
    void blocksKnownIpBeforeAnyApplicationHandlerRuns() throws Exception {
        IpBlockService blocked = mock(IpBlockService.class);
        when(blocked.isBlocked("198.51.100.7")).thenReturn(true);
        RequestBoundaryFilter localFilter = new RequestBoundaryFilter(new SecurityProperties(
                List.of("app.example"), List.of()), blocked, signals);
        var request = request("GET", "app.example");
        request.setRemoteAddr("198.51.100.7");
        var response = new MockHttpServletResponse();
        var chain = new MockFilterChain();

        localFilter.doFilter(request, response, chain);

        assertThat(response.getStatus()).isEqualTo(403);
        assertThat(chain.getRequest()).isNull();
        verify(signals, never()).record(org.mockito.ArgumentMatchers.any(), anyString(), anyString());
    }

    @Test
    void treatsSafeCrossSiteReadsAsReadOnlyAndRecordsMalformedOrigins() throws Exception {
        var read = request("GET", "app.example");
        read.addHeader("Sec-Fetch-Site", "cross-site");
        var readResponse = new MockHttpServletResponse();
        filter.doFilter(read, readResponse, new MockFilterChain());
        assertThat(readResponse.getStatus()).isEqualTo(200);

        var malformed = request("POST", "app.example");
        malformed.addHeader("Origin", "not an origin");
        var malformedResponse = new MockHttpServletResponse();
        filter.doFilter(malformed, malformedResponse, new MockFilterChain());
        assertThat(malformedResponse.getStatus()).isEqualTo(403);
        verify(signals).record(malformed, "reconnaissance", "cross_site");
    }

    private static MockHttpServletRequest request(String method, String host) {
        var request = new MockHttpServletRequest(method, "/api/auth/login");
        request.setServerName(host);
        return request;
    }

    private RequestBoundaryFilter filter(SecurityProperties properties) {
        return new RequestBoundaryFilter(properties, ipBlocks, signals);
    }

    private static IpBlockService unblockedIpService() {
        IpBlockService service = mock(IpBlockService.class);
        when(service.isBlocked(anyString())).thenReturn(false);
        return service;
    }
}
