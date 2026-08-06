package eu.royalblackwater.api.account.filter;

import eu.royalblackwater.api.shared.filter.ListFilter;
import java.util.Map;
import java.util.Set;

public record UserAdministrationFilter(ListFilter page, String role, String status, Long fleetId) {
    public static UserAdministrationFilter from(Map<String, Object> parameters) {
        return new UserAdministrationFilter(
                ListFilter.from(parameters, 100, 500),
                ListFilter.optionalEnum(parameters, "role", Set.of("user", "moderator", "admin")),
                ListFilter.optionalEnum(parameters, "status", Set.of("active", "inactive", "all")),
                ListFilter.optionalPositiveLong(parameters, "fleet_id"));
    }
}
