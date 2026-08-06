package eu.royalblackwater.api.squads.filter;

import eu.royalblackwater.api.shared.filter.ListFilter;
import java.util.Map;

public record SquadListFilter(ListFilter page, Long fleetId, boolean includeInactive, boolean mineOnly) {
    public static SquadListFilter from(Map<String, Object> parameters) {
        return new SquadListFilter(
                ListFilter.from(parameters, 100, 250),
                ListFilter.optionalPositiveLong(parameters, "fleet_id"),
                parameters.get("include_inactive") instanceof Boolean value && value,
                false);
    }

    public static SquadListFilter mine() {
        return new SquadListFilter(new ListFilter(null, 250, 0), null, false, true);
    }
}
