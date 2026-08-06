package eu.royalblackwater.api.account.service;

import eu.royalblackwater.api.account.entity.AuthSessionEntity;
import eu.royalblackwater.api.account.entity.UserEntity;
import eu.royalblackwater.api.account.mapper.AuthenticationDtoMapper;
import eu.royalblackwater.api.account.repository.AuthSessionRepository;
import eu.royalblackwater.api.account.repository.UserRepository;
import eu.royalblackwater.api.config.SessionProperties;
import eu.royalblackwater.api.security.dto.AuthenticatedUser;
import eu.royalblackwater.api.security.service.PasswordHasher;
import eu.royalblackwater.api.security.service.SessionTokenService;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Locale;
import java.util.Optional;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuthService {
    private final UserRepository users;
    private final AuthSessionRepository sessions;
    private final PasswordHasher passwords;
    private final SessionTokenService tokens;
    private final SessionProperties properties;
    private final Clock clock;
    private final AuthenticationDtoMapper mapper;

    public AuthService(UserRepository users, AuthSessionRepository sessions, PasswordHasher passwords,
                       SessionTokenService tokens, SessionProperties properties, Clock clock,
                       AuthenticationDtoMapper mapper) {
        this.users = users;
        this.sessions = sessions;
        this.passwords = passwords;
        this.tokens = tokens;
        this.properties = properties;
        this.clock = clock;
        this.mapper = mapper;
    }

    @Transactional
    public Optional<LoginResult> login(String username, String password) {
        Optional<UserEntity> found = users.findByUsername(username.strip().toLowerCase(Locale.ROOT));
        if (found.isEmpty() || !found.get().isActive() || !passwords.verify(password, found.get().getPasswordHash())) {
            return Optional.empty();
        }
        UserEntity user = found.get();
        if (passwords.needsRehash(user.getPasswordHash())) user.setPasswordHash(passwords.hash(password));
        return Optional.of(new LoginResult(user.getId(), createSession(user)));
    }

    @Transactional
    public Optional<AuthenticatedUser> authenticatedUser(String rawToken) {
        return authenticatedEntity(rawToken).map(mapper::toAuthenticatedUser);
    }

    private Optional<UserEntity> authenticatedEntity(String rawToken) {
        if (rawToken == null || rawToken.isBlank()) return Optional.empty();
        Optional<AuthSessionEntity> found = sessions.findByTokenHash(tokens.hash(rawToken));
        if (found.isEmpty()) return Optional.empty();
        AuthSessionEntity session = found.get();
        if (!session.getExpiresAt().isAfter(now())) {
            sessions.delete(session);
            return Optional.empty();
        }
        Optional<UserEntity> user = users.findAuthenticatedById(session.getUser().getId());
        if (user.isEmpty() || !user.get().isActive()) return Optional.empty();
        return user;
    }

    @Transactional
    public Optional<Integer> authenticatedUserId(String rawToken) {
        return authenticatedUser(rawToken).map(AuthenticatedUser::id);
    }

    @Transactional
    public void logout(String rawToken) {
        if (rawToken != null && !rawToken.isBlank()) sessions.deleteByTokenHash(tokens.hash(rawToken));
    }

    @Transactional
    public Optional<String> changePassword(String rawToken, String currentPassword, String newPassword) {
        Optional<UserEntity> authenticated = authenticatedEntity(rawToken);
        if (authenticated.isEmpty() || !passwords.verify(currentPassword, authenticated.get().getPasswordHash())) {
            return Optional.empty();
        }
        UserEntity user = authenticated.get();
        user.setPasswordHash(passwords.hash(newPassword));
        sessions.deleteByUserId(user.getId());
        return Optional.of(createSession(user));
    }

    private String createSession(UserEntity user) {
        String raw = tokens.create();
        LocalDateTime now = now();
        sessions.save(new AuthSessionEntity(tokens.hash(raw), user, now.plus(properties.ttl()), now));
        return raw;
    }

    private LocalDateTime now() { return LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC); }
    public record LoginResult(int userId, String token) { }
}
