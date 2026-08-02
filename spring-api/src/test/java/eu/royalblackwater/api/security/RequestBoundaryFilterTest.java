package eu.royalblackwater.api.security;

import static org.assertj.core.api.Assertions.assertThat;
import eu.royalblackwater.api.config.SecurityProperties;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockFilterChain;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

class RequestBoundaryFilterTest {
    private final RequestBoundaryFilter filter = new RequestBoundaryFilter(new SecurityProperties(
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

    private static MockHttpServletRequest request(String method, String host) {
        var request = new MockHttpServletRequest(method, "/api/auth/login");
        request.setServerName(host);
        return request;
    }
}
