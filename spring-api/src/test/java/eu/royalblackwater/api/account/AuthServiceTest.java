package eu.royalblackwater.api.account;

import eu.royalblackwater.api.account.entity.AuthSessionEntity;
import eu.royalblackwater.api.account.entity.UserEntity;
import eu.royalblackwater.api.account.mapper.AuthenticationDtoMapper;
import eu.royalblackwater.api.account.repository.AuthSessionRepository;
import eu.royalblackwater.api.account.repository.UserRepository;
import eu.royalblackwater.api.account.service.AuthService;
import eu.royalblackwater.api.config.SessionProperties;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.PasswordHasher;
import eu.royalblackwater.api.security.service.SessionTokenService;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class AuthServiceTest {
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2030-01-15T12:00:00Z"), ZoneOffset.UTC);
    private static final LocalDateTime NOW = LocalDateTime.ofInstant(CLOCK.instant(), ZoneOffset.UTC);

    @Test
    void loginNormalizesUsernameRehashesPasswordAndCreatesExpiringSession() {
        UserRepository users = mock(UserRepository.class);
        AuthSessionRepository sessions = mock(AuthSessionRepository.class);
        PasswordHasher passwords = mock(PasswordHasher.class);
        SessionTokenService tokens = mock(SessionTokenService.class);
        AuthenticationDtoMapper mapper = mock(AuthenticationDtoMapper.class);
        UserEntity user = mock(UserEntity.class);
        when(user.getId()).thenReturn(42);
        when(user.isActive()).thenReturn(true);
        when(user.getPasswordHash()).thenReturn("old-hash");
        when(users.findByUsername("captain")).thenReturn(Optional.of(user));
        when(passwords.verify("secret", "old-hash")).thenReturn(true);
        when(passwords.needsRehash("old-hash")).thenReturn(true);
        when(passwords.hash("secret")).thenReturn("new-password-hash");
        when(tokens.create()).thenReturn("raw-session");
        when(tokens.hash("raw-session")).thenReturn("session-hash");

        AuthService service = service(users, sessions, passwords, tokens, mapper);
        var result = service.login("  CAPTAIN  ", "secret");

        assertThat(result).contains(new AuthService.LoginResult(42, "raw-session"));
        verify(user).setPasswordHash("new-password-hash");
        ArgumentCaptor<AuthSessionEntity> saved = ArgumentCaptor.forClass(AuthSessionEntity.class);
        verify(sessions).save(saved.capture());
        assertThat(saved.getValue().getUser()).isSameAs(user);
        assertThat(saved.getValue().getExpiresAt()).isEqualTo(NOW.plusHours(4));
    }

    @Test
    void loginRejectsMissingInactiveAndInvalidPasswordUsersWithoutCreatingSessions() {
        UserRepository users = mock(UserRepository.class);
        AuthSessionRepository sessions = mock(AuthSessionRepository.class);
        PasswordHasher passwords = mock(PasswordHasher.class);
        SessionTokenService tokens = mock(SessionTokenService.class);
        AuthenticationDtoMapper mapper = mock(AuthenticationDtoMapper.class);
        AuthService service = service(users, sessions, passwords, tokens, mapper);

        when(users.findByUsername("missing")).thenReturn(Optional.empty());
        assertThat(service.login("missing", "secret")).isEmpty();

        UserEntity inactive = mock(UserEntity.class);
        when(inactive.isActive()).thenReturn(false);
        when(users.findByUsername("inactive")).thenReturn(Optional.of(inactive));
        assertThat(service.login("inactive", "secret")).isEmpty();

        UserEntity invalid = mock(UserEntity.class);
        when(invalid.isActive()).thenReturn(true);
        when(invalid.getPasswordHash()).thenReturn("hash");
        when(users.findByUsername("invalid")).thenReturn(Optional.of(invalid));
        when(passwords.verify("wrong", "hash")).thenReturn(false);
        assertThat(service.login("invalid", "wrong")).isEmpty();

        verify(tokens, never()).create();
        verify(sessions, never()).save(org.mockito.ArgumentMatchers.any());
    }

    @Test
    void expiredSessionIsDeletedAndCannotAuthenticate() {
        UserRepository users = mock(UserRepository.class);
        AuthSessionRepository sessions = mock(AuthSessionRepository.class);
        PasswordHasher passwords = mock(PasswordHasher.class);
        SessionTokenService tokens = mock(SessionTokenService.class);
        AuthenticationDtoMapper mapper = mock(AuthenticationDtoMapper.class);
        AuthSessionEntity session = mock(AuthSessionEntity.class);
        when(tokens.hash("expired")).thenReturn("expired-hash");
        when(sessions.findByTokenHash("expired-hash")).thenReturn(Optional.of(session));
        when(session.getExpiresAt()).thenReturn(NOW.minusSeconds(1));

        assertThat(service(users, sessions, passwords, tokens, mapper).authenticatedUser("expired")).isEmpty();
        verify(sessions).delete(session);
        verify(users, never()).findAuthenticatedById(org.mockito.ArgumentMatchers.any());
    }

    @Test
    void validSessionMapsAuthenticatedUser() {
        UserRepository users = mock(UserRepository.class);
        AuthSessionRepository sessions = mock(AuthSessionRepository.class);
        PasswordHasher passwords = mock(PasswordHasher.class);
        SessionTokenService tokens = mock(SessionTokenService.class);
        AuthenticationDtoMapper mapper = mock(AuthenticationDtoMapper.class);
        AuthSessionEntity session = mock(AuthSessionEntity.class);
        UserEntity user = mock(UserEntity.class);
        AuthenticatedUser expected = new AuthenticatedUser(7, "captain", "member", false, false, false);
        when(tokens.hash("valid")).thenReturn("valid-hash");
        when(sessions.findByTokenHash("valid-hash")).thenReturn(Optional.of(session));
        when(session.getExpiresAt()).thenReturn(NOW.plusMinutes(5));
        when(session.getUser()).thenReturn(user);
        when(user.getId()).thenReturn(7);
        when(users.findAuthenticatedById(7)).thenReturn(Optional.of(user));
        when(user.isActive()).thenReturn(true);
        when(mapper.toAuthenticatedUser(user)).thenReturn(expected);

        AuthService service = service(users, sessions, passwords, tokens, mapper);
        assertThat(service.authenticatedUser("valid")).contains(expected);
        assertThat(service.authenticatedUserId("valid")).contains(7);
    }

    @Test
    void passwordChangeRotatesAllExistingSessionsAndReturnsFreshToken() {
        UserRepository users = mock(UserRepository.class);
        AuthSessionRepository sessions = mock(AuthSessionRepository.class);
        PasswordHasher passwords = mock(PasswordHasher.class);
        SessionTokenService tokens = mock(SessionTokenService.class);
        AuthenticationDtoMapper mapper = mock(AuthenticationDtoMapper.class);
        AuthSessionEntity session = mock(AuthSessionEntity.class);
        UserEntity user = mock(UserEntity.class);
        when(tokens.hash("old-token")).thenReturn("old-token-hash");
        when(sessions.findByTokenHash("old-token-hash")).thenReturn(Optional.of(session));
        when(session.getExpiresAt()).thenReturn(NOW.plusMinutes(30));
        when(session.getUser()).thenReturn(user);
        when(user.getId()).thenReturn(9);
        when(users.findAuthenticatedById(9)).thenReturn(Optional.of(user));
        when(user.isActive()).thenReturn(true);
        when(user.getPasswordHash()).thenReturn("old-password-hash");
        when(passwords.verify("old-password", "old-password-hash")).thenReturn(true);
        when(passwords.hash("new-password")).thenReturn("new-password-hash");
        when(tokens.create()).thenReturn("fresh-token");
        when(tokens.hash("fresh-token")).thenReturn("fresh-token-hash");

        var result = service(users, sessions, passwords, tokens, mapper)
                .changePassword("old-token", "old-password", "new-password");

        assertThat(result).contains("fresh-token");
        verify(user).setPasswordHash("new-password-hash");
        verify(sessions).deleteByUserId(9);
        verify(sessions).save(org.mockito.ArgumentMatchers.any(AuthSessionEntity.class));
    }

    @Test
    void logoutIgnoresBlankTokensAndDeletesHashedNonBlankTokens() {
        UserRepository users = mock(UserRepository.class);
        AuthSessionRepository sessions = mock(AuthSessionRepository.class);
        PasswordHasher passwords = mock(PasswordHasher.class);
        SessionTokenService tokens = mock(SessionTokenService.class);
        AuthenticationDtoMapper mapper = mock(AuthenticationDtoMapper.class);
        AuthService service = service(users, sessions, passwords, tokens, mapper);

        service.logout(null);
        service.logout("   ");
        verify(tokens, never()).hash(org.mockito.ArgumentMatchers.anyString());

        when(tokens.hash("token")).thenReturn("token-hash");
        service.logout("token");
        verify(sessions).deleteByTokenHash("token-hash");
    }

    private static AuthService service(UserRepository users, AuthSessionRepository sessions, PasswordHasher passwords,
                                       SessionTokenService tokens, AuthenticationDtoMapper mapper) {
        return new AuthService(users, sessions, passwords, tokens,
                new SessionProperties("rbf_hub_session", false, "Lax", Duration.ofHours(4)), CLOCK, mapper);
    }
}
