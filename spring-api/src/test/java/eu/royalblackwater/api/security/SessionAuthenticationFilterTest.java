package eu.royalblackwater.api.security;

import eu.royalblackwater.api.account.service.AuthService;
import eu.royalblackwater.api.config.SessionProperties;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.filter.SessionAuthenticationFilter;
import jakarta.servlet.http.Cookie;
import java.time.Duration;
import java.util.Optional;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockFilterChain;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

class SessionAuthenticationFilterTest {
    private final AuthService auth = mock(AuthService.class);
    private final SessionAuthenticationFilter filter = new SessionAuthenticationFilter(
            auth, new SessionProperties("rbf_session", true, "Strict", Duration.ofHours(8)));

    @AfterEach
    void clearSecurityContext() {
        SecurityContextHolder.clearContext();
    }

    @Test
    void matchingSessionCookieAuthenticatesPrincipalAndDerivedAuthorities() throws Exception {
        AuthenticatedUser user = new AuthenticatedUser(7, "captain", "admin", true, true, true);
        when(auth.authenticatedUser("token-1")).thenReturn(Optional.of(user));
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/auth/me");
        request.setCookies(new Cookie("other", "ignored"), new Cookie("rbf_session", "token-1"));
        MockFilterChain chain = new MockFilterChain();

        filter.doFilter(request, new MockHttpServletResponse(), chain);

        var authentication = SecurityContextHolder.getContext().getAuthentication();
        assertThat(authentication).isNotNull();
        assertThat(authentication.getPrincipal()).isSameAs(user);
        assertThat(authentication.getAuthorities()).extracting(Object::toString)
                .containsExactly("ROLE_ADMIN", "RBF_STAFF", "RBF_SYSTEM");
        verify(auth).authenticatedUser("token-1");
        assertThat(chain.getRequest()).isSameAs(request);
    }

    @Test
    void memberSessionGetsPortalAuthorityAndNoCookieUsesNullLookup() throws Exception {
        AuthenticatedUser user = new AuthenticatedUser(8, "member", "user", false, false, false);
        when(auth.authenticatedUser(null)).thenReturn(Optional.of(user));
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/auth/me");

        filter.doFilter(request, new MockHttpServletResponse(), new MockFilterChain());

        assertThat(SecurityContextHolder.getContext().getAuthentication().getAuthorities())
                .extracting(Object::toString)
                .containsExactly("ROLE_USER", "RBF_MEMBER", "RBF_PORTAL");
        verify(auth).authenticatedUser(null);
    }

    @Test
    void existingSecurityContextSkipsSessionLookup() throws Exception {
        var existing = UsernamePasswordAuthenticationToken.authenticated(
                "existing", null, java.util.List.of());
        SecurityContextHolder.getContext().setAuthentication(existing);

        filter.doFilter(new MockHttpServletRequest("GET", "/api/auth/me"),
                new MockHttpServletResponse(), new MockFilterChain());

        assertThat(SecurityContextHolder.getContext().getAuthentication()).isSameAs(existing);
        verifyNoInteractions(auth);
    }

    @Test
    void unknownSessionLeavesRequestAnonymous() throws Exception {
        when(auth.authenticatedUser("missing")).thenReturn(Optional.empty());
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/api/auth/me");
        request.setCookies(new Cookie("rbf_session", "missing"));

        filter.doFilter(request, new MockHttpServletResponse(), new MockFilterChain());

        assertThat(SecurityContextHolder.getContext().getAuthentication()).isNull();
    }
}
