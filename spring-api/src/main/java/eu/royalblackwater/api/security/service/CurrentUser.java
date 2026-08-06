package eu.royalblackwater.api.security.service;

import eu.royalblackwater.api.security.model.AuthenticatedUser;
import java.util.Optional;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.UNAUTHORIZED;

public final class CurrentUser {
    private CurrentUser() { }

    public static Optional<AuthenticatedUser> optional() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !(authentication.getPrincipal() instanceof AuthenticatedUser principal)) {
            return Optional.empty();
        }
        return Optional.of(principal);
    }

    public static AuthenticatedUser require() {
        return optional().orElseThrow(() -> new ResponseStatusException(UNAUTHORIZED, "Authentication required."));
    }
}
