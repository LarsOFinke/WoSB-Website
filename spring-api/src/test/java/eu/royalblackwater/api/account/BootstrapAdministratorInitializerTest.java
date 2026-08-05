package eu.royalblackwater.api.account;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import eu.royalblackwater.api.config.BootstrapAdminProperties;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.security.PasswordHasher;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

class BootstrapAdministratorInitializerTest {
    @Test
    void repairsFleetLeadershipForAnExistingAdministratorWithoutRequiringTheBootstrapPassword() {
        JdbcQueryService jdbc = mock(JdbcQueryService.class);
        PasswordHasher passwords = mock(PasswordHasher.class);
        when(jdbc.optional(anyString(), anyMap())).thenAnswer(invocation -> {
            String sql = invocation.getArgument(0);
            if (sql.contains("is_bootstrap_admin=true")) return Optional.of(Map.of("id", 7L));
            if (sql.contains("from fleets")) return Optional.of(Map.of("id", 11L));
            if (sql.contains("from fleet_roles")) return Optional.of(Map.of("id", 13L));
            return Optional.empty();
        });
        var initializer = new BootstrapAdministratorInitializer(
                jdbc, passwords, new BootstrapAdminProperties("admin", "", "RBF Command"),
                Clock.fixed(Instant.parse("2026-08-05T12:00:00Z"), ZoneOffset.UTC));

        initializer.initialize();

        verify(passwords, never()).hash(anyString());
        verify(jdbc, never()).insertReturningId(anyString(), anyMap());
        ArgumentCaptor<String> sql = ArgumentCaptor.forClass(String.class);
        @SuppressWarnings("unchecked")
        ArgumentCaptor<Map<String, ?>> parameters = ArgumentCaptor.forClass(Map.class);
        verify(jdbc, org.mockito.Mockito.times(2)).update(sql.capture(), parameters.capture());
        assertThat(sql.getAllValues().get(1)).contains("insert into fleet_memberships", "on conflict(user_id)");
        Map<String, ?> fleetParameters = parameters.getAllValues().get(1);
        assertThat(fleetParameters.get("userId")).isEqualTo(7L);
        assertThat(fleetParameters.get("fleetId")).isEqualTo(11L);
        assertThat(fleetParameters.get("roleId")).isEqualTo(13L);
    }
}
