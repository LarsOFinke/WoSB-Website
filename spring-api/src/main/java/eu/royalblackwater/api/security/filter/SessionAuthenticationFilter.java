package eu.royalblackwater.api.security.filter;

import eu.royalblackwater.api.account.service.AuthService;
import eu.royalblackwater.api.config.SessionProperties;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.List;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
public class SessionAuthenticationFilter extends OncePerRequestFilter {
    private final AuthService authentication;
    private final SessionProperties session;

    public SessionAuthenticationFilter(AuthService authentication, SessionProperties session) {
        this.authentication = authentication;
        this.session = session;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        if (SecurityContextHolder.getContext().getAuthentication() == null) {
            authentication.authenticatedUser(rawToken(request)).ifPresent(this::authenticate);
        }
        chain.doFilter(request, response);
    }

    private void authenticate(AuthenticatedUser principal) {
        var authorities = List.of(
                new SimpleGrantedAuthority(principal.authority()),
                new SimpleGrantedAuthority(principal.staff() ? "RBF_STAFF" : "RBF_MEMBER"),
                new SimpleGrantedAuthority(principal.canManageSystem() ? "RBF_SYSTEM" : "RBF_PORTAL"));
        SecurityContextHolder.getContext().setAuthentication(
                UsernamePasswordAuthenticationToken.authenticated(principal, null, authorities));
    }

    private String rawToken(HttpServletRequest request) {
        Cookie[] cookies = request.getCookies();
        if (cookies == null) {
            return null;
        }
        for (Cookie cookie : cookies) {
            if (session.cookieName().equals(cookie.getName())) {
                return cookie.getValue();
            }
        }
        return null;
    }
}
