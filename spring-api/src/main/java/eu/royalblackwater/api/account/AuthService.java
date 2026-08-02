package eu.royalblackwater.api.account;

import eu.royalblackwater.api.config.SessionProperties;
import eu.royalblackwater.api.security.PasswordHasher;
import eu.royalblackwater.api.security.SessionTokenService;
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
    private final Clock clock = Clock.systemUTC();

    public AuthService(UserRepository users, AuthSessionRepository sessions, PasswordHasher passwords,
                       SessionTokenService tokens, SessionProperties properties) {
        this.users = users;
        this.sessions = sessions;
        this.passwords = passwords;
        this.tokens = tokens;
        this.properties = properties;
    }

    @Transactional
    public Optional<LoginResult> login(String username, String password) {
        Optional<UserEntity> found = users.findByUsername(username.strip().toLowerCase(Locale.ROOT));
        if (found.isEmpty() || !found.get().isActive() || !passwords.verify(password, found.get().getPasswordHash())) {
            return Optional.empty();
        }
        UserEntity user = found.get();
        if (passwords.needsRehash(user.getPasswordHash())) user.setPasswordHash(passwords.hash(password));
        return Optional.of(new LoginResult(user, createSession(user)));
    }

    @Transactional
    public Optional<UserEntity> authenticatedUser(String rawToken) {
        if (rawToken == null || rawToken.isBlank()) return Optional.empty();
        Optional<AuthSessionEntity> found = sessions.findByTokenHash(tokens.hash(rawToken));
        if (found.isEmpty()) return Optional.empty();
        AuthSessionEntity session = found.get();
        if (!session.getExpiresAt().isAfter(now())) {
            sessions.delete(session);
            return Optional.empty();
        }
        return session.getUser().isActive() ? Optional.of(session.getUser()) : Optional.empty();
    }

    @Transactional
    public void logout(String rawToken) {
        if (rawToken != null && !rawToken.isBlank()) sessions.deleteByTokenHash(tokens.hash(rawToken));
    }

    @Transactional
    public Optional<String> changePassword(String rawToken, String currentPassword, String newPassword) {
        Optional<UserEntity> authenticated = authenticatedUser(rawToken);
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
    public record LoginResult(UserEntity user, String token) { }
}
