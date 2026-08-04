package eu.royalblackwater.api.core;

import eu.royalblackwater.api.persistence.JdbcQueryService;
import eu.royalblackwater.api.transport.AbstractApiOperationHandler;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.flywaydb.core.Flyway;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.SERVICE_UNAVAILABLE;

@Component
public class CoreOperationHandler extends AbstractApiOperationHandler {
    private static final Set<String> OPERATIONS = Set.of(
            "get_home_api_home_get",
            "health_check_api_health_get",
            "readiness_check_api_health_ready_get");
    private final JdbcQueryService jdbc;
    private final Flyway flyway;

    public CoreOperationHandler(JdbcQueryService jdbc, Flyway flyway) {
        this.jdbc = jdbc;
        this.flyway = flyway;
    }

    @Override
    public Set<String> operations() { return OPERATIONS; }

    @Override
    protected Object execute(String operationId, Map<String, Object> parameters, Object body, MultipartFile upload) {
        return switch (operationId) {
            case "health_check_api_health_get" -> Map.of("status", "ok");
            case "readiness_check_api_health_ready_get" -> readiness();
            case "get_home_api_home_get" -> home();
            default -> throw new IllegalStateException("Unsupported core operation: " + operationId);
        };
    }

    private Map<String, String> readiness() {
        try {
            jdbc.count("select 1", Map.of());
            if (flyway.info().pending().length != 0) {
                throw new IllegalStateException("Database migrations are pending.");
            }
            flyway.validate();
            return Map.of("status", "ready");
        } catch (RuntimeException exception) {
            throw new ResponseStatusException(SERVICE_UNAVAILABLE, "Database is not ready.", exception);
        }
    }

    private static Map<String, Object> home() {
        return Map.of(
                "route", "/home",
                "title", "Royal Blackwater Fleet",
                "focus", "newcomer_onboarding_and_fleet_operations",
                "activity_window", Map.of("timezone", "CET", "main", "12:00-02:00", "port_battles", "18:00-23:00"),
                "voice_policy", Map.of("competitive", "required", "general", "optional_encouraged"),
                "modules", List.of(
                        Map.of("key", "builds", "status", "available", "access", "member"),
                        Map.of("key", "guides", "status", "available", "access", "member"),
                        Map.of("key", "forum", "status", "available", "access", "member"),
                        Map.of("key", "calendar", "status", "available", "access", "member"),
                        Map.of("key", "groups", "status", "available", "access", "member")));
    }
}
