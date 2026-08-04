package eu.royalblackwater.api.squads;

import eu.royalblackwater.api.transport.ListFilter;
import java.util.Map;

record SquadListFilter(ListFilter page, Long fleetId, boolean includeInactive, boolean mineOnly) {
    static SquadListFilter from(Map<String, Object> parameters) {
        return new SquadListFilter(
                ListFilter.from(parameters, 100, 250),
                ListFilter.optionalPositiveLong(parameters, "fleet_id"),
                parameters.get("include_inactive") instanceof Boolean value && value,
                false);
    }

    static SquadListFilter mine() {
        return new SquadListFilter(new ListFilter(null, 250, 0), null, false, true);
    }
}
