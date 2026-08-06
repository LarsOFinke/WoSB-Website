package eu.royalblackwater.api.account.filter;

import eu.royalblackwater.api.shared.filter.ListFilter;
import java.util.Set;

public record UserAdministrationFilter(ListFilter page, String role, String status, Long fleetId) {
    public static UserAdministrationFilter from(
            String search, String role, String status, Long fleetId, long limit, long offset) {
        return new UserAdministrationFilter(
                ListFilter.of(search, limit, offset, 500),
                ListFilter.optionalEnum(role, "role", Set.of("user", "moderator", "admin")),
                ListFilter.optionalEnum(status, "status", Set.of("active", "inactive", "all")),
                ListFilter.optionalPositiveLong(fleetId, "fleet_id"));
    }
}
