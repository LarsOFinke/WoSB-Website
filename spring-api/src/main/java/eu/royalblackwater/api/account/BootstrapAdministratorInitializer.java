package eu.royalblackwater.api.account;

import eu.royalblackwater.api.config.BootstrapAdminProperties;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.security.PasswordHasher;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Map;
import java.util.Locale;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class BootstrapAdministratorInitializer {
    private final JdbcQueryService jdbc;
    private final PasswordHasher passwords;
    private final BootstrapAdminProperties properties;
    private final Clock clock;

    public BootstrapAdministratorInitializer(JdbcQueryService jdbc, PasswordHasher passwords,
                                               BootstrapAdminProperties properties, Clock clock) {
        this.jdbc = jdbc;
        this.passwords = passwords;
        this.properties = properties;
        this.clock = clock;
    }

    @Order(20)
    @EventListener(ApplicationReadyEvent.class)
    @Transactional
    public void initialize() {
        long existing = jdbc.count("select count(*) from users where is_bootstrap_admin=true", Map.of());
        if (existing > 0) return;
        if (!properties.configured()) {
            throw new IllegalStateException("SEED_ADMIN_PASSWORD is required until a bootstrap administrator exists.");
        }
        String username = properties.username().toLowerCase(Locale.ROOT);
        if (jdbc.count("select count(*) from users where username=:username", Map.of("username", username)) > 0) {
            throw new IllegalStateException("Bootstrap administrator username is already in use.");
        }
        LocalDateTime now = LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC);
        long userId = jdbc.insertReturningId("""
                insert into users(username,password_hash,site_role_id,is_active,is_bootstrap_admin,created_at,updated_at)
                values(:username,:password,(select id from site_roles where code='admin'),true,true,:now,:now)
                returning id
                """, Map.of("username", username, "password", passwords.hash(properties.password()), "now", now));
        jdbc.update("""
                insert into user_profiles(user_id,display_name,created_at,updated_at)
                values(:userId,:displayName,:now,:now)
                """, Map.of("userId", userId, "displayName", properties.displayName(), "now", now));
    }
}
