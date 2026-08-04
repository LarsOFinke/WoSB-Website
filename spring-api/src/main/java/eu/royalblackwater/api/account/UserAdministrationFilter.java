package eu.royalblackwater.api.account;

import eu.royalblackwater.api.transport.ListFilter;
import java.util.Map;
import java.util.Set;

record UserAdministrationFilter(ListFilter page, String role, String status, Long fleetId) {
    static UserAdministrationFilter from(Map<String, Object> parameters) {
        return new UserAdministrationFilter(
                ListFilter.from(parameters, 100, 500),
                ListFilter.optionalEnum(parameters, "role", Set.of("user", "moderator", "admin")),
                ListFilter.optionalEnum(parameters, "status", Set.of("active", "inactive", "all")),
                ListFilter.optionalPositiveLong(parameters, "fleet_id"));
    }
}
