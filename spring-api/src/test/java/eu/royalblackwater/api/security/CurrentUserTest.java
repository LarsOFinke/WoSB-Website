package eu.royalblackwater.api.security;

import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.CurrentUser;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.server.ResponseStatusException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class CurrentUserTest {
    @AfterEach
    void clearContext() {
        SecurityContextHolder.clearContext();
    }

    @Test
    void optionalAndRequireUseOnlyTypedAuthenticatedPrincipals() {
        assertThat(CurrentUser.optional()).isEmpty();
        assertThatThrownBy(CurrentUser::require).isInstanceOf(ResponseStatusException.class)
                .satisfies(error -> assertThat(((ResponseStatusException) error).getStatusCode().value()).isEqualTo(401));

        AuthenticatedUser actor = new AuthenticatedUser(7, "captain", "member", false, false, false);
        SecurityContextHolder.getContext().setAuthentication(
                new UsernamePasswordAuthenticationToken(actor, null, java.util.List.of()));
        assertThat(CurrentUser.optional()).contains(actor);
        assertThat(CurrentUser.require()).isSameAs(actor);
    }
}
