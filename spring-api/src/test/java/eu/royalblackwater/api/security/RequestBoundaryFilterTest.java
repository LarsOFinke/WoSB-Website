package eu.royalblackwater.api.security;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import eu.royalblackwater.api.config.SecurityProperties;
import eu.royalblackwater.api.securityops.IpBlockService;
import eu.royalblackwater.api.securityops.SecuritySignalService;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockFilterChain;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

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
