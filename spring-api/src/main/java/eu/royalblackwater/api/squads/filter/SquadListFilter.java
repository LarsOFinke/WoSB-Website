package eu.royalblackwater.api.squads.filter;

import eu.royalblackwater.api.shared.filter.ListFilter;

public record SquadListFilter(ListFilter page, Long fleetId, boolean includeInactive, boolean mineOnly) {
    public static SquadListFilter from(
            String search, Long fleetId, boolean includeInactive, long limit, long offset) {
        return new SquadListFilter(
                ListFilter.of(search, limit, offset, 250),
                ListFilter.optionalPositiveLong(fleetId, "fleet_id"),
                includeInactive,
                false);
    }

    public static SquadListFilter mine() {
        return new SquadListFilter(new ListFilter(null, 250, 0), null, false, true);
    }
}
