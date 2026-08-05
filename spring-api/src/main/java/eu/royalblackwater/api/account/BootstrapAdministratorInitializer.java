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
        LocalDateTime now = LocalDateTime.ofInstant(clock.instant(), ZoneOffset.UTC);
        Map<String, Object> existing = jdbc.optional("""
                select id from users where is_bootstrap_admin=true order by id limit 1
                """, Map.of()).orElse(null);
        long userId = existing == null ? createAdministrator(now) : ((Number) existing.get("id")).longValue();
        jdbc.update("""
                insert into user_profiles(user_id,display_name,created_at,updated_at)
                values(:userId,:displayName,:now,:now)
                on conflict(user_id) do nothing
                """, Map.of("userId", userId, "displayName", properties.displayName(), "now", now));
        ensureFleetLeadership(userId, now);
    }

    private long createAdministrator(LocalDateTime now) {
        if (!properties.configured()) {
            throw new IllegalStateException("SEED_ADMIN_PASSWORD is required until a bootstrap administrator exists.");
        }
        String username = properties.username().toLowerCase(Locale.ROOT);
        if (jdbc.count("select count(*) from users where username=:username", Map.of("username", username)) > 0) {
            throw new IllegalStateException("Bootstrap administrator username is already in use.");
        }
        return jdbc.insertReturningId("""
                insert into users(username,password_hash,site_role_id,is_active,is_bootstrap_admin,created_at,updated_at)
                values(:username,:password,(select id from site_roles where code='admin'),true,true,:now,:now)
                returning id
                """, Map.of("username", username, "password", passwords.hash(properties.password()), "now", now));
    }

    private void ensureFleetLeadership(long userId, LocalDateTime now) {
        long fleetId = requiredSeedId("fleets", "slug", "royal-blackwater-fleet");
        long roleId = requiredSeedId("fleet_roles", "code", "fleet_admiral");
        jdbc.update("""
                insert into fleet_memberships
                    (fleet_id,user_id,fleet_role_id,status,joined_at,updated_at)
                values(:fleetId,:userId,:roleId,'active',:now,:now)
                on conflict(user_id) do update set fleet_id=excluded.fleet_id,
                    fleet_role_id=excluded.fleet_role_id,status='active',updated_at=excluded.updated_at
                where fleet_memberships.fleet_id is distinct from excluded.fleet_id
                   or fleet_memberships.fleet_role_id is distinct from excluded.fleet_role_id
                   or fleet_memberships.status is distinct from 'active'
                """, Map.of("fleetId", fleetId, "userId", userId, "roleId", roleId, "now", now));
    }

    private long requiredSeedId(String table, String column, String value) {
        if (!("fleets".equals(table) && "slug".equals(column))
                && !("fleet_roles".equals(table) && "code".equals(column))) {
            throw new IllegalArgumentException("Unsupported bootstrap seed lookup.");
        }
        return jdbc.optional("select id from " + table + " where " + column + "=:value", Map.of("value", value))
                .map(row -> ((Number) row.get("id")).longValue())
                .orElseThrow(() -> new IllegalStateException("Required bootstrap seed is missing: " + value));
    }
}
