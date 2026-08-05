package eu.royalblackwater.api.securityops;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import eu.royalblackwater.api.contract.SecurityDashboard;
import eu.royalblackwater.api.persistence.JdbcQueryService;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

class SecurityDashboardServiceTest {
    @Test
    void convertsJdbcDateValuesAtThePersistenceBoundary() {
        JdbcQueryService jdbc = mock(JdbcQueryService.class);
        LocalDate day = LocalDate.of(2026, 8, 5);
        when(jdbc.query(anyString(), anyMap())).thenReturn(List.of(Map.of(
                "id", 1L,
                "day", java.sql.Date.valueOf(day),
                "client_ip", "192.0.2.1",
                "signal", "login_failure",
                "reason", "invalid_credentials",
                "request_target", "/api/auth/login",
                "event_count", 2L)));
        Clock clock = Clock.fixed(Instant.parse("2026-08-05T12:00:00Z"), ZoneOffset.UTC);

        SecurityDashboard result = new SecurityDashboardService(jdbc, clock)
                .build(day, day, null, null, "threat", 100);

        assertThat(result.ips()).singleElement().satisfies(row -> {
            assertThat(row.firstSeen()).isEqualTo(day);
            assertThat(row.lastSeen()).isEqualTo(day);
        });
        assertThat(result.days()).singleElement().satisfies(bucket ->
                assertThat(bucket.day()).isEqualTo(day));
    }
}
