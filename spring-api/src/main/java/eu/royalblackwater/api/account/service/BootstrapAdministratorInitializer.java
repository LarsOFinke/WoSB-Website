package eu.royalblackwater.api.account.service;

import eu.royalblackwater.api.account.repository.AccountDataRepository;
import eu.royalblackwater.api.account.repository.queries.BootstrapAdministratorQueries;
import eu.royalblackwater.api.config.BootstrapAdminProperties;
import eu.royalblackwater.api.security.service.PasswordHasher;
import java.time.Clock;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Locale;
import java.util.Map;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class BootstrapAdministratorInitializer {
    private final AccountDataRepository repository;
    private final PasswordHasher passwords;
    private final BootstrapAdminProperties properties;
    private final Clock clock;

    public BootstrapAdministratorInitializer(AccountDataRepository repository, PasswordHasher passwords,
                                               BootstrapAdminProperties properties, Clock clock) {
        this.repository = repository;
        this.passwords = passwords;
        this.properties = properties;
        this.clock = clock;
    }

    @Order(20)
    @EventListener(ApplicationReadyEvent.class)
    @Transactional
    public void initialize() {
        LocalDateTime now = LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC);
        Map<String, Object> existing = repository.optional(BootstrapAdministratorQueries.INITIALIZE_SELECT_01, Map.of()).orElse(null);
        long userId = existing == null ? createAdministrator(now) : ((Number) existing.get("id")).longValue();
        repository.update(BootstrapAdministratorQueries.INITIALIZE_INSERT_01, Map.of("userId", userId, "displayName", properties.displayName(), "now", now));
        ensureFleetLeadership(userId, now);
    }

    private long createAdministrator(LocalDateTime now) {
        if (!properties.configured()) {
            throw new IllegalStateException("SEED_ADMIN_PASSWORD is required until a bootstrap administrator exists.");
        }
        String username = properties.username().toLowerCase(Locale.ROOT);
        if (repository.count(BootstrapAdministratorQueries.CREATE_ADMINISTRATOR_SELECT_01, Map.of("username", username)) > 0) {
            throw new IllegalStateException("Bootstrap administrator username is already in use.");
        }
        return repository.insertReturningId(BootstrapAdministratorQueries.CREATE_ADMINISTRATOR_INSERT_01, Map.of("username", username, "password", passwords.hash(properties.password()), "now", now));
    }

    private void ensureFleetLeadership(long userId, LocalDateTime now) {
        long fleetId = requiredSeedId("fleets", "slug", "royal-blackwater-fleet");
        long roleId = requiredSeedId("fleet_roles", "code", "fleet_admiral");
        repository.update(BootstrapAdministratorQueries.ENSURE_FLEET_LEADERSHIP_INSERT_01, Map.of("fleetId", fleetId, "userId", userId, "roleId", roleId, "now", now));
    }

    private long requiredSeedId(String table, String column, String value) {
        if (!("fleets".equals(table) && "slug".equals(column))
                && !("fleet_roles".equals(table) && "code".equals(column))) {
            throw new IllegalArgumentException("Unsupported bootstrap seed lookup.");
        }
        return repository.optional(BootstrapAdministratorQueries.REQUIRED_SEED_ID_SELECT_01 + table + BootstrapAdministratorQueries.REQUIRED_SEED_ID_WHERE_01 + column + "=:value", Map.of("value", value))
                .map(row -> ((Number) row.get("id")).longValue())
                .orElseThrow(() -> new IllegalStateException("Required bootstrap seed is missing: " + value));
    }
}
