package eu.royalblackwater.api.security;

import eu.royalblackwater.api.security.filter.CsrfCookieFilter;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.security.web.csrf.CsrfToken;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;

class CsrfCookieFilterTest {
    private final CsrfCookieFilter filter = new CsrfCookieFilter();

    @Test
    void materializesDeferredTokenBeforeContinuingTheChain() throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/auth/me");
        MockHttpServletResponse response = new MockHttpServletResponse();
        boolean[] called = {false};
        CsrfToken token = mock(CsrfToken.class);
        request.setAttribute(CsrfToken.class.getName(), token);

        filter.doFilter(request, response, (chainRequest, chainResponse) -> called[0] = true);

        verify(token).getToken();
        assertThat(called[0]).isTrue();
    }

    @Test
    void missingCsrfAttributeDoesNotBlockSafeRequests() throws Exception {
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/health");
        MockHttpServletResponse response = new MockHttpServletResponse();
        boolean[] called = {false};

        filter.doFilter(request, response, (chainRequest, chainResponse) -> called[0] = true);

        assertThat(called[0]).isTrue();
        assertThat(response.getStatus()).isEqualTo(200);
    }
}
